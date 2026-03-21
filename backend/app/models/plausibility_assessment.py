from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.models.enums import RiskTier, RoutingDecision


class PlausibilityAssessment(Base):
    __tablename__ = "plausibility_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), nullable=False, unique=True)
    plausibility_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_tier: Mapped[RiskTier] = mapped_column(Enum(RiskTier), nullable=False)
    signals: Mapped[dict] = mapped_column(JSON, nullable=False)
    routing_decision: Mapped[RoutingDecision] = mapped_column(Enum(RoutingDecision), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    claim = relationship("Claim", back_populates="plausibility_assessment")
