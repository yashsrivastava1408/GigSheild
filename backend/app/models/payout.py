from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.models.enums import PaymentMethod, PayoutStatus


class Payout(Base):
    __tablename__ = "payouts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), nullable=False, unique=True)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    razorpay_payment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[PayoutStatus] = mapped_column(Enum(PayoutStatus), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    claim = relationship("Claim", back_populates="payout")
    worker = relationship("Worker", back_populates="payouts")
