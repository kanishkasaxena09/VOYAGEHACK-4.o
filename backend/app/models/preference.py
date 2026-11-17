import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class TripPreference(Base):
    __tablename__ = "trip_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    hotel_category: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    preferred_airline: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    cabin_class: Mapped[Optional[str]] = mapped_column(
        String(50), default="economy", nullable=True
    )
    nonstop_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    max_flight_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    food_preferences: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    activity_preferences: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    pace: Mapped[Optional[str]] = mapped_column(
        String(50), default="relaxed", nullable=True
    )
    accessibility_requirements: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    things_to_avoid: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    extra_preferences: Mapped[Optional[dict]] = mapped_column(
        JSON, default=dict, nullable=True
    )

    trip = relationship("Trip", back_populates="preferences")


class ConstraintSeverity(str):
    HARD = "HARD"
    SOFT = "SOFT"


class TripConstraint(Base):
    __tablename__ = "trip_constraints"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    constraint_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., MAX_BUDGET, NO_REDEYE, NONSTOP_REQUIRED, MAX_TRAVEL_TIME
    value: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(20), default=ConstraintSeverity.HARD, nullable=False
    )  # HARD or SOFT
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    trip = relationship("Trip", back_populates="constraints")
