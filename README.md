# Lab Report Automation — Dhivya & Sagar

A development-ready starter for the assigned Lab Report Automation module.

## Team technology stack
- React.js + JavaScript + Tailwind CSS (frontend)
- Python FastAPI (backend REST API)
- Supabase PostgreSQL + private Supabase Storage (production integration)
- SQLite + local files (local demo fallback)
- n8n (WhatsApp notification, critical email and voice-call workflow)
- OpenRouter (optional patient-friendly rewrite of doctor-provided notes)
- Git/GitHub

**Note on the supplied project guide:** the Notion setup guide mentions Gemini for note simplification; your team leader's stack screenshot specifies OpenRouter. This implementation uses OpenRouter for the same narrow text-rewriting task. It does not diagnose, interpret lab values, prescribe, or recommend treatment.

## What it does
1. Staff enters patient name/phone/report type, doctor-provided note and critical flag, then uploads a PDF.
2. FastAPI validates the PDF, saves it locally in demo mode or to a private Supabase Storage bucket when enabled.
3. Backend creates a random secure token with a 7-day expiry and stores report metadata.
4. Optional OpenRouter call rewrites only the supplied doctor note in simple language; if unavailable, original note is retained.
5. Backend posts a report-ready event to n8n.
6. n8n sends the approved WhatsApp `report_ready` template. If staff marked the report critical, it also sends an admin email and triggers the configured voice server.
7. Patient accesses the PDF through the tokenized URL; expired/invalid links are rejected.

## Run locally (no credentials needed for demo)
### Backend
```bash
cd backend
python -m venv venv
# Windows: venv\\Scripts\\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # Windows; macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000 | Swagger: http://127.0.0.1:8000/docs

### Frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Local mode uses SQLite and local PDF storage.

## Supabase setup (Sagar's integration)
1. Create a Supabase project and run `supabase/schema.sql` in SQL Editor.
2. Create a **private** Storage bucket named `lab-reports`.
3. Copy `backend/.env.example` to `backend/.env` and set `DATABASE_MODE=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_STORAGE_BUCKET=lab-reports`.
4. Restart FastAPI. The service-role key must stay server-side; never put it in React or commit `.env` to GitHub.

## OpenRouter setup
Set `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in backend `.env`. Only doctor-provided note text is sent in this starter. Confirm hospital privacy approval before sending any real patient information to an external AI provider.

## n8n setup
1. Import `n8n/lab_report_automation_workflow.json` using Workflows → Import from File.
2. Configure the WhatsApp HTTP node with Meta Cloud API credentials and an approved `report_ready` template with parameters: `{{1}}` patient name, `{{2}}` report type, `{{3}}` secure view link.
3. Configure SMTP credentials for the email node and your approved voice server URL/token for the voice node.
4. Activate workflow, copy its production webhook URL into `N8N_LAB_REPORT_WEBHOOK_URL` in backend `.env`.
5. Set n8n timezone to `Asia/Kolkata`.

## API
- `GET /api/health` — health check
- `POST /api/reports` — multipart PDF upload and report creation
- `GET /api/reports` — recent report list for staff dashboard
- `GET /api/public/reports/{token}` — validate token and return patient-facing metadata
- `GET /api/public/reports/{token}/file` — serve PDF after token/expiry check
- `POST /api/webhooks/n8n/test` — test n8n event connection

## Important
This is a project prototype, not a production-certified hospital system. Add staff authentication/RBAC, audit logs, malware scanning, rate limits, consent, encryption/key management, backup/retention rules and a security review before production. Critical status must be set by authorized clinical staff, never by AI. Do not diagnose, interpret results, prescribe medication or dosage. Do not use real patient data until the hospital approves the privacy/security design.
