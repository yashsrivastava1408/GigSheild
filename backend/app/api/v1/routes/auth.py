from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import AuthSessionResponse, OtpRequest, OtpRequestResponse, OtpVerifyRequest
from app.services.auth import request_login_otp, verify_login_otp


router = APIRouter()


@router.post("/request-otp", response_model=OtpRequestResponse)
async def request_otp(payload: OtpRequest, db: Session = Depends(get_db)) -> OtpRequestResponse:
    return request_login_otp(db, payload.phone)


@router.post("/verify-otp", response_model=AuthSessionResponse)
async def verify_otp(payload: OtpVerifyRequest, db: Session = Depends(get_db)) -> AuthSessionResponse:
    return verify_login_otp(db, payload.phone, payload.otp_code)
