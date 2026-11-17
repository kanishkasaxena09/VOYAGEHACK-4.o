import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class DisruptionStatus(str):
    DETECTED = "DETECTED"
    OPTIONS_PRESENTED = "OPTIONS_PRESENTED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Disruption(Base):
    __tablename__ = "disruptions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    disruption_type: Mapped[str] = mapped_column(
        String(100), nullable=False  # FLIGHT_CANCELLED, FLIGHT_DELAYED, HOTEL_UNAVAILABLE, etc.
    )
    target_type: Mapped[str] = mapped_column(
        String(50), nullable=False  # FLIGHT, HOTEL, ACTIVITY, TRANSFER
    )
    reference_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(20), default="HIGH", nullable=False  # LOW, MEDIUM, HIGH, CRITICAL
    )
    reason: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default=DisruptionStatus.DETECTED, index=True, nullable=False
    )
    impact_summary: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    original_data: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )
    alternative_options: Mapped[List[dict]] = mapped_column(
        JSON, default=list, nullable=False
    )
    selected_option: Mapped[Optional[dict]] = mapped_column(
        JSON, default=dict, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    trip = relationship("Trip", back_populates="disruptions")
