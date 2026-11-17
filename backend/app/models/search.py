import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class SearchResult(Base):
    __tablename__ = "search_results"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False  # FLIGHT, HOTEL, ACTIVITY, TRANSFER
    )
    provider: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    external_id: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
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
    available: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    cancellation_policy: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    penalty_fee: Mapped[Optional[float]] = mapped_column(
        Float, default=0.0, nullable=True
    )
    details: Mapped[dict] = mapped_column(
        JSON, default=dict, nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_stale: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    trip = relationship("Trip", back_populates="search_results")
