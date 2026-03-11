from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ClaimStatus


class FraudLog(Base):
    __tablename__ = "fraud_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"), nullable=False)
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), nullable=False)
    fraud_type: Mapped[str] = mapped_column(String(100), nullable=False)
    fraud_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    signals: Mapped[dict] = mapped_column(JSON, nullable=False)
    action_taken: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
