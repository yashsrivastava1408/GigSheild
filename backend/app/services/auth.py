import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import access_token_expiry, ensure_utc, generate_otp_code, generate_session_token, otp_expiry
from app.models.auth_session import AuthSession
from app.models.otp_challenge import OtpChallenge
from app.repositories.auth import (
    create_auth_session,
    create_otp_challenge,
    delete_auth_sessions_for_worker,
    get_latest_active_otp,
    mark_otp_consumed,
)
from app.repositories.workers import get_worker_by_phone
from app.schemas.auth import AuthSessionResponse, OtpRequestResponse
from app.schemas.worker import WorkerResponse
from app.services.providers import send_otp_sms


def request_login_otp(db: Session, phone: str) -> OtpRequestResponse:
    worker = get_worker_by_phone(db, phone)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found for this phone.")

    challenge = OtpChallenge(
        id=str(uuid.uuid4()),
        phone=phone,
        otp_code=generate_otp_code(),
        expires_at=otp_expiry(),
    )
    create_otp_challenge(db, challenge)
    delivery = send_otp_sms(phone, challenge.otp_code)
    return OtpRequestResponse(
        challenge_id=challenge.id,
        expires_in_minutes=settings.otp_ttl_minutes,
        delivery_mode=delivery.delivery_mode,
        mock_otp_code=challenge.otp_code if settings.use_mock_sms else None,
    )


def verify_login_otp(db: Session, phone: str, otp_code: str) -> AuthSessionResponse:
    worker = get_worker_by_phone(db, phone)
    if worker is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Worker not found for this phone.")

    challenge = get_latest_active_otp(db, phone)
    if challenge is None or ensure_utc(challenge.expires_at) < datetime.now(UTC) or challenge.otp_code != otp_code:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired OTP.")

    mark_otp_consumed(db, challenge)
    delete_auth_sessions_for_worker(db, worker.id)
    token = generate_session_token(worker.id)
    create_auth_session(
        db,
        AuthSession(
            id=str(uuid.uuid4()),
            worker_id=worker.id,
            token=token,
            expires_at=access_token_expiry(),
        ),
    )

    return AuthSessionResponse(access_token=token, worker=WorkerResponse.model_validate(worker))
