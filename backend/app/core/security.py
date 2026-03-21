import hashlib
import hmac
import secrets
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import UTC, utcnow
from app.db.session import get_db
from app.repositories.auth import get_auth_session_by_token
from app.repositories.workers import get_worker_by_id


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def generate_session_token(worker_id: str) -> str:
    nonce = secrets.token_urlsafe(24)
    payload = f"{worker_id}.{nonce}".encode()
    signature = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).hexdigest()
    return f"{worker_id}.{nonce}.{signature}"


def generate_admin_token() -> str:
    nonce = secrets.token_urlsafe(24)
    expires_at = int((utcnow() + timedelta(minutes=settings.admin_token_ttl_minutes)).timestamp())
    payload = f"admin.{nonce}.{expires_at}".encode()
    signature = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).hexdigest()
    return f"admin.{nonce}.{expires_at}.{signature}"


def verify_admin_token(token: str) -> bool:
    try:
        subject, nonce, expires_at_raw, signature = token.split(".", 3)
    except ValueError:
        return False
    if subject != "admin":
        return False
    payload = f"{subject}.{nonce}.{expires_at_raw}".encode()
    expected = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return False
    return int(expires_at_raw) >= int(utcnow().timestamp())


def verify_session_token(token: str) -> bool:
    try:
        worker_id, nonce, signature = token.split(".", 2)
    except ValueError:
        return False
    payload = f"{worker_id}.{nonce}".encode()
    expected = hmac.new(settings.secret_key.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


def access_token_expiry() -> datetime:
    return utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)


def otp_expiry() -> datetime:
    return utcnow() + timedelta(minutes=settings.otp_ttl_minutes)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def get_current_worker(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")
    token = authorization.replace("Bearer ", "", 1).strip()
    if not verify_session_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token.")

    session = get_auth_session_by_token(db, token)
    if session is None or ensure_utc(session.expires_at) < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired.")

    worker = get_worker_by_id(db, session.worker_id)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Worker not found.")
    return worker


def require_admin(
    authorization: str | None = Header(default=None),
) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing admin bearer token.")
    token = authorization.replace("Bearer ", "", 1).strip()
    if not verify_admin_token(token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access denied.")
