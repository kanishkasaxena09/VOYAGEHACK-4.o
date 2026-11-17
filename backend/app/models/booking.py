import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class BookingStatus(str):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    MODIFIED = "MODIFIED"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    booking_reference: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default=BookingStatus.PENDING, index=True, nullable=False
    )
    total_amount: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="INR", nullable=False
    )
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    cancellation_policy: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    penalty_fee: Mapped[Optional[float]] = mapped_column(
        Float, default=0.0, nullable=True
    )
    refund_amount: Mapped[Optional[float]] = mapped_column(
        Float, default=0.0, nullable=True
    )
    voucher_data: Mapped[Optional[dict]] = mapped_column(
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

    trip = relationship("Trip", back_populates="bookings")
    items = relationship("BookingItem", back_populates="booking", lazy="selectin", cascade="all, delete-orphan")


class BookingItem(Base):
    __tablename__ = "booking_items"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("bookings.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False  # FLIGHT, HOTEL, ACTIVITY, TRANSFER
    )
    provider: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    provider_booking_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    price: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="INR", nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="CONFIRMED", nullable=False
    )
    cancellation_policy: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    details: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )

    booking = relationship("Booking", back_populates="items")
