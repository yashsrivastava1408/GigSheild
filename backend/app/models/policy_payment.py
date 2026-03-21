from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.models.enums import CoverageTier, PolicyPaymentStatus


class PolicyPayment(Base):
    __tablename__ = "policy_payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"), nullable=False)
    policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("policies.id"), nullable=True)
    coverage_tier: Mapped[CoverageTier] = mapped_column(Enum(CoverageTier), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    razorpay_order_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    status: Mapped[PolicyPaymentStatus] = mapped_column(Enum(PolicyPaymentStatus), nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    worker = relationship("Worker", back_populates="policy_payments")
    policy = relationship("Policy")
