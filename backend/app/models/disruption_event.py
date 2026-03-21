from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.db.base import Base
from app.models.enums import DisruptionEventType


class DisruptionEvent(Base):
    __tablename__ = "disruption_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[DisruptionEventType] = mapped_column(Enum(DisruptionEventType), nullable=False)
    zone_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    weather_api_raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    claims = relationship("Claim", back_populates="disruption_event")
