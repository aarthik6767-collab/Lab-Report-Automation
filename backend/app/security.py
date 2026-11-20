import secrets
from datetime import datetime, timedelta, timezone
from .config import settings

def new_token() -> str:
    return secrets.token_urlsafe(32)

def expiry_time() -> str:
    return (datetime.now(timezone.utc) + timedelta(days=max(settings.token_ttl_days, 1))).isoformat()

def expired(value: str) -> bool:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) <= datetime.now(timezone.utc)
