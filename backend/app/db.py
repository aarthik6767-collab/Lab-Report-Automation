import sqlite3
from pathlib import Path
import httpx
from .config import settings

def local_conn():
    p = Path(settings.local_database_path)
    if not p.is_absolute(): p = Path(__file__).resolve().parents[1] / p
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(p); c.row_factory = sqlite3.Row
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
      id TEXT PRIMARY KEY, patient_name TEXT, patient_phone TEXT, report_type TEXT,
      storage_path TEXT, secure_token TEXT UNIQUE, expires_at TEXT, is_critical INTEGER,
      doctor_notes TEXT, friendly_note TEXT, created_at TEXT)''')
    c.commit(); return c

def sb(method, table, **kwargs):
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env")
    h={"apikey":settings.supabase_service_role_key,"Authorization":f"Bearer {settings.supabase_service_role_key}","Content-Type":"application/json"}
    h.update(kwargs.pop("headers",{}))
    r=httpx.request(method,f"{settings.supabase_url.rstrip('/')}/rest/v1/{table}",headers=h,timeout=25,**kwargs); r.raise_for_status()
    return r.json() if r.content else None

def save(row):
    if settings.database_mode == "supabase": sb("POST","reports",json=row,headers={"Prefer":"return=representation"}); return
    c=local_conn()
    try:
      c.execute('''INSERT INTO reports VALUES (:id,:patient_name,:patient_phone,:report_type,:storage_path,:secure_token,:expires_at,:is_critical,:doctor_notes,:friendly_note,:created_at)''',row); c.commit()
    finally: c.close()

def by_token(token):
    if settings.database_mode == "supabase":
      rows=sb("GET","reports",params={"select":"*","secure_token":f"eq.{token}","limit":"1"}); return rows[0] if rows else None
    c=local_conn()
    try:
      x=c.execute("SELECT * FROM reports WHERE secure_token=?",(token,)).fetchone(); return dict(x) if x else None
    finally: c.close()

def recent():
    if settings.database_mode == "supabase": return sb("GET","reports",params={"select":"id,patient_name,report_type,is_critical,created_at,expires_at","order":"created_at.desc","limit":"50"})
    c=local_conn()
    try: return [dict(x) for x in c.execute("SELECT id,patient_name,report_type,is_critical,created_at,expires_at FROM reports ORDER BY created_at DESC LIMIT 50").fetchall()]
    finally: c.close()
