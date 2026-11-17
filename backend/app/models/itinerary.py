import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tier: Mapped[str] = mapped_column(
        String(50), nullable=False  # Budget, Balanced, Premium
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    total_estimated_cost: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="INR", nullable=False
    )
    is_selected: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    highlights: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    trip = relationship("Trip", back_populates="itineraries")
    items = relationship("ItineraryItem", back_populates="itinerary", lazy="selectin", cascade="all, delete-orphan", order_by="ItineraryItem.day_number")


class ItineraryItem(Base):
    __tablename__ = "itinerary_items"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    itinerary_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("itineraries.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day_number: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    location: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    morning: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    afternoon: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    evening: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    activities: Mapped[List[dict]] = mapped_column(
        JSON, default=list, nullable=False
    )
    hotel: Mapped[Optional[dict]] = mapped_column(
        JSON, default=dict, nullable=True
    )
    transport: Mapped[Optional[dict]] = mapped_column(
        JSON, default=dict, nullable=True
    )
    estimated_cost: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    travel_time_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    itinerary = relationship("Itinerary", back_populates="items")
