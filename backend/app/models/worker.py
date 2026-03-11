from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Platform


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    phone: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[Platform] = mapped_column(Enum(Platform), nullable=False)
    zone_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trust_score: Mapped[float] = mapped_column(Numeric(5, 2), default=75.00, nullable=False)
    avg_weekly_earnings: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tenure_days: Mapped[int] = mapped_column(default=0, nullable=False)
    kyc_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    policies = relationship("Policy", back_populates="worker")
    claims = relationship("Claim", back_populates="worker")
    payouts = relationship("Payout", back_populates="worker")
