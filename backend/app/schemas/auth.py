from pydantic import BaseModel, Field

from app.schemas.worker import WorkerResponse


class OtpRequest(BaseModel):
    phone: str = Field(pattern=r"^\d{10}$")


class OtpRequestResponse(BaseModel):
    challenge_id: str
    expires_in_minutes: int
    delivery_mode: str
    mock_otp_code: str | None = None


class OtpVerifyRequest(BaseModel):
    phone: str = Field(pattern=r"^\d{10}$")
    otp_code: str = Field(pattern=r"^\d{6}$")


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    worker: WorkerResponse
