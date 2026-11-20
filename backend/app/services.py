from pathlib import Path
import uuid, httpx
from .config import settings

async def save_pdf(data: bytes, filename: str) -> str:
    name=f"{uuid.uuid4().hex}_{Path(filename).name.replace(' ','_')}"
    if settings.database_mode == "supabase":
      url=f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{settings.supabase_storage_bucket}/{name}"
      headers={"apikey":settings.supabase_service_role_key,"Authorization":f"Bearer {settings.supabase_service_role_key}","Content-Type":"application/pdf","x-upsert":"false"}
      async with httpx.AsyncClient(timeout=60) as c:
        r=await c.post(url,content=data,headers=headers); r.raise_for_status()
      return f"supabase://{settings.supabase_storage_bucket}/{name}"
    folder=Path(settings.local_upload_dir)
    if not folder.is_absolute(): folder=Path(__file__).resolve().parents[1]/folder
    folder.mkdir(parents=True,exist_ok=True); p=folder/name; p.write_bytes(data); return str(p)

async def read_pdf(path: str) -> bytes:
    if path.startswith("supabase://"):
      bucket,obj=path.removeprefix("supabase://").split("/",1); url=f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{obj}"
      h={"apikey":settings.supabase_service_role_key,"Authorization":f"Bearer {settings.supabase_service_role_key}"}
      async with httpx.AsyncClient(timeout=60) as c:
        r=await c.get(url,headers=h); r.raise_for_status(); return r.content
    return Path(path).read_bytes()

async def simplify_note(note: str):
    if not note.strip(): return "", "No doctor note supplied"
    if not settings.openrouter_api_key: return note, "OpenRouter not configured; original note retained"
    payload={"model":settings.openrouter_model,"temperature":0.2,"max_tokens":300,"messages":[
      {"role":"system","content":"Rewrite the clinician-provided note in simple patient-friendly English. Do not diagnose, interpret lab values, recommend treatment, prescribe medicines or dosage, or add facts. Preserve uncertainty and say the patient should discuss the report with their doctor."},
      {"role":"user","content":note[:4000]}]}
    headers={"Authorization":f"Bearer {settings.openrouter_api_key}","Content-Type":"application/json","HTTP-Referer":settings.report_portal_base_url,"X-Title":"Lab Report Automation"}
    try:
      async with httpx.AsyncClient(timeout=30) as c:
        r=await c.post(f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",json=payload,headers=headers); r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip(), "OpenRouter note rewrite completed"
    except Exception: return note, "OpenRouter unavailable; original doctor note retained"

async def send_n8n(payload: dict):
    if not settings.n8n_lab_report_webhook_url: return "not_configured"
    try:
      async with httpx.AsyncClient(timeout=settings.n8n_webhook_timeout_seconds) as c:
        r=await c.post(settings.n8n_lab_report_webhook_url,json=payload); r.raise_for_status()
      return "accepted"
    except Exception: return "failed"
