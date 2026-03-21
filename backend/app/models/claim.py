from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.models.enums import ClaimStatus


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(36), ForeignKey("policies.id"), nullable=False)
    worker_id: Mapped[str] = mapped_column(String(36), ForeignKey("workers.id"), nullable=False)
    disruption_event_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("disruption_events.id"),
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus), nullable=False)
    fraud_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    trust_score_at_claim: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    policy = relationship("Policy", back_populates="claims")
    worker = relationship("Worker", back_populates="claims")
    disruption_event = relationship("DisruptionEvent", back_populates="claims")
    payout = relationship("Payout", back_populates="claim", uselist=False)
    plausibility_assessment = relationship("PlausibilityAssessment", back_populates="claim", uselist=False)
