from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Lab Report Automation API"
    frontend_origin: str = "http://localhost:5173"
    backend_public_url: str = "http://127.0.0.1:8000"
    report_portal_base_url: str = "http://localhost:5173"
    token_ttl_days: int = 7
    max_upload_mb: int = 10
    database_mode: str = "local"
    local_database_path: str = "./lab_reports.db"
    local_upload_dir: str = "./uploads"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "lab-reports"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    n8n_lab_report_webhook_url: str = ""
    n8n_webhook_timeout_seconds: int = 15
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
