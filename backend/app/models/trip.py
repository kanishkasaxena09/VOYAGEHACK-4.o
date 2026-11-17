import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class TripStatus(str):
    INSPIRATION = "INSPIRATION"
    PLANNING = "PLANNING"
    READY_TO_BOOK = "READY_TO_BOOK"
    BOOKED = "BOOKED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255), default="My Upcoming Trip", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default=TripStatus.INSPIRATION, index=True, nullable=False
    )
    origin: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    destination: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    start_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )
    duration_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    number_of_travellers: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False
    )
    budget_amount: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    budget_currency: Mapped[str] = mapped_column(
        String(10), default="INR", nullable=False
    )
    purpose: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    interests: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    pace: Mapped[Optional[str]] = mapped_column(
        String(50), default="relaxed", nullable=True
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

    # Relationships with lazy="selectin" to prevent MissingGreenlet in async sessions
    user = relationship("User", back_populates="trips")
    travellers = relationship("Traveller", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    preferences = relationship("TripPreference", back_populates="trip", uselist=False, lazy="selectin", cascade="all, delete-orphan")
    constraints = relationship("TripConstraint", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    recommendations = relationship("DestinationRecommendation", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    itineraries = relationship("Itinerary", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    search_results = relationship("SearchResult", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    pending_actions = relationship("PendingAction", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    disruptions = relationship("Disruption", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="trip", lazy="selectin", cascade="all, delete-orphan")
