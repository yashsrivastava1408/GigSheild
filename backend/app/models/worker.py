from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.models.enums import PaymentMethod, PayoutProfileStatus, Platform


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    phone: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    zone_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    trust_score: Mapped[float] = mapped_column(Numeric(5, 2), default=75.00, nullable=False)
    avg_weekly_earnings: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tenure_days: Mapped[int] = mapped_column(default=0, nullable=False)
    kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payout_method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod), nullable=True)
    payout_upi_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payout_bank_account_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payout_bank_account_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    payout_bank_ifsc: Mapped[str | None] = mapped_column(String(16), nullable=True)
    payout_contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payout_contact_phone: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payout_fund_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payout_profile_status: Mapped[PayoutProfileStatus] = mapped_column(
        Enum(PayoutProfileStatus),
        default=PayoutProfileStatus.missing,
        nullable=False,
    )
    payout_profile_review_notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payout_profile_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    policies = relationship("Policy", back_populates="worker")
    claims = relationship("Claim", back_populates="worker")
    payouts = relationship("Payout", back_populates="worker")
    policy_payments = relationship("PolicyPayment", back_populates="worker")
    zone_observations = relationship("WorkerZoneObservation", back_populates="worker")
