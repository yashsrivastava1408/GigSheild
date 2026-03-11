from datetime import UTC, date, datetime, timedelta

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CoverageTier, PolicyStatus


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"), nullable=False)
    coverage_tier: Mapped[CoverageTier] = mapped_column(Enum(CoverageTier), nullable=False)
    weekly_premium: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    coverage_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, default=lambda: date.today() + timedelta(days=6), nullable=False)
    status: Mapped[PolicyStatus] = mapped_column(Enum(PolicyStatus), default=PolicyStatus.active, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    worker = relationship("Worker", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")
