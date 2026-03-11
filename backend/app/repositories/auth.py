from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.auth_session import AuthSession
from app.models.otp_challenge import OtpChallenge


def create_otp_challenge(db: Session, challenge: OtpChallenge) -> OtpChallenge:
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def get_latest_active_otp(db: Session, phone: str) -> OtpChallenge | None:
    statement = (
        select(OtpChallenge)
        .where(OtpChallenge.phone == phone, OtpChallenge.consumed.is_(False))
        .order_by(OtpChallenge.created_at.desc())
    )
    return db.scalar(statement)


def mark_otp_consumed(db: Session, challenge: OtpChallenge) -> OtpChallenge:
    challenge.consumed = True
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def create_auth_session(db: Session, session: AuthSession) -> AuthSession:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_auth_session_by_token(db: Session, token: str) -> AuthSession | None:
    return db.scalar(select(AuthSession).where(AuthSession.token == token))


def delete_auth_sessions_for_worker(db: Session, worker_id: str) -> None:
    db.execute(delete(AuthSession).where(AuthSession.worker_id == worker_id))
    db.commit()
