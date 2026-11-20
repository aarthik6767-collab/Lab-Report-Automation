from datetime import datetime, timezone
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .config import settings
from .db import save, by_token, recent
from .security import new_token, expiry_time, expired
from .services import save_pdf, read_pdf, simplify_note, send_n8n

app=FastAPI(title=settings.app_name,version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=[settings.frontend_origin,"http://localhost:5173"],allow_methods=["*"],allow_headers=["*"],allow_credentials=True)

@app.get("/api/health")
def health(): return {"status":"ok","database_mode":settings.database_mode}

@app.post("/api/reports")
async def create_report(patient_name:str=Form(...),patient_phone:str=Form(...),report_type:str=Form(...),doctor_notes:str=Form(""),is_critical:bool=Form(False),file:UploadFile=File(...)):
    if not all(x.strip() for x in [patient_name,patient_phone,report_type]): raise HTTPException(400,"Patient name, phone and report type are required")
    if not (file.filename or "").lower().endswith(".pdf"): raise HTTPException(415,"Only PDF files are accepted")
    data=await file.read()
    if not data or len(data)>settings.max_upload_mb*1024*1024: raise HTTPException(413,f"PDF must be under {settings.max_upload_mb} MB")
    if not data.startswith(b"%PDF"): raise HTTPException(400,"Uploaded file is not a valid PDF")
    try:
      storage=await save_pdf(data,file.filename or "report.pdf"); friendly,note_status=await simplify_note(doctor_notes)
      token=new_token(); expiry=expiry_time(); rid=str(uuid.uuid4()); created=datetime.now(timezone.utc).isoformat()
      row={"id":rid,"patient_name":patient_name.strip(),"patient_phone":patient_phone.strip(),"report_type":report_type.strip(),"storage_path":storage,"secure_token":token,"expires_at":expiry,"is_critical":bool(is_critical),"doctor_notes":doctor_notes.strip(),"friendly_note":friendly,"created_at":created}
      save(row)
      link=f"{settings.report_portal_base_url.rstrip('/')}/report/{token}"
      event={"event":"lab_report_ready","report_id":rid,"patient_name":row["patient_name"],"patient_phone":row["patient_phone"],"report_type":row["report_type"],"secure_view_link":link,"expires_at":expiry,"is_critical":bool(is_critical),"doctor_friendly_note":friendly,"created_at":created}
      n8n_status=await send_n8n(event)
      return {"id":rid,"patient_name":row["patient_name"],"report_type":row["report_type"],"status":"ready","secure_link":link,"expires_at":expiry,"n8n_status":n8n_status,"note_status":note_status}
    except HTTPException: raise
    except Exception as e: raise HTTPException(500,f"Report processing failed: {e}")

@app.get("/api/reports")
def reports():
    try: return {"reports":recent()}
    except Exception as e: raise HTTPException(500,str(e))

@app.get("/api/public/reports/{token}")
def public_report(token:str):
    row=by_token(token)
    if not row: raise HTTPException(404,"Invalid report link")
    if expired(row["expires_at"]): raise HTTPException(410,"This report link has expired. Contact the hospital.")
    return {"patient_name":row["patient_name"],"report_type":row["report_type"],"doctor_friendly_note":row.get("friendly_note") or row.get("doctor_notes") or "Please discuss your report with your doctor.","expires_at":row["expires_at"],"file_url":f"{settings.backend_public_url.rstrip('/')}/api/public/reports/{token}/file","message":"This page provides report access only, not medical advice."}

@app.get("/api/public/reports/{token}/file")
async def public_file(token:str):
    row=by_token(token)
    if not row: raise HTTPException(404,"Invalid report link")
    if expired(row["expires_at"]): raise HTTPException(410,"This report link has expired")
    try: return Response(await read_pdf(row["storage_path"]),media_type="application/pdf",headers={"Content-Disposition":"inline; filename=lab-report.pdf","Cache-Control":"no-store"})
    except Exception: raise HTTPException(404,"Report file unavailable")

@app.post("/api/webhooks/n8n/test")
async def test_n8n(): return {"n8n_status":await send_n8n({"event":"lab_report_test","message":"Test from Lab Report Automation"})}
