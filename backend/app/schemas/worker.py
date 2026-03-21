from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.enums import PaymentMethod, PayoutProfileStatus, Platform


class WorkerCreateRequest(BaseModel):
    phone: str = Field(pattern=r"^\d{10}$")
    name: str = Field(min_length=2, max_length=100)
    platform: Platform
    zone_id: str = Field(min_length=2, max_length=64)
    device_fingerprint: str | None = Field(default=None, min_length=8, max_length=128)
    avg_weekly_earnings: float = Field(gt=0)
    tenure_days: int = Field(ge=0, default=0)
    kyc_verified: bool = False


class WorkerResponse(BaseModel):
    id: str
    phone: str
    name: str
    platform: Platform
    zone_id: str
    trust_score: float
    avg_weekly_earnings: float
    tenure_days: int
    kyc_verified: bool
    payout_method: PaymentMethod | None = None
    payout_upi_id: str | None = None
    payout_bank_account_name: str | None = None
    payout_bank_account_number: str | None = None
    payout_bank_ifsc: str | None = None
    payout_contact_name: str | None = None
    payout_contact_phone: str | None = None
    payout_profile_status: PayoutProfileStatus
    payout_profile_review_notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkerPayoutProfileUpdateRequest(BaseModel):
    payout_method: PaymentMethod
    payout_upi_id: str | None = Field(default=None, max_length=100)
    payout_bank_account_name: str | None = Field(default=None, min_length=2, max_length=100)
    payout_bank_account_number: str | None = Field(default=None, min_length=6, max_length=32)
    payout_bank_ifsc: str | None = Field(default=None, min_length=4, max_length=16)
    payout_contact_name: str = Field(min_length=2, max_length=100)
    payout_contact_phone: str = Field(pattern=r"^\d{10}$")

    @model_validator(mode="after")
    def validate_destination(self):
        if self.payout_method == PaymentMethod.upi and not self.payout_upi_id:
            raise ValueError("UPI ID is required for UPI payouts.")
        if self.payout_method == PaymentMethod.bank_transfer:
            if not self.payout_bank_account_name or not self.payout_bank_account_number or not self.payout_bank_ifsc:
                raise ValueError("Bank payout requires account name, account number, and IFSC.")
        return self


class AdminPayoutProfileReviewRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=255)
