import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class DestinationRecommendation(Base):
    __tablename__ = "destination_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    destination: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    fit_score: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    why_it_fits: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    tradeoffs: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )
    estimated_cost: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(10), default="INR", nullable=False
    )
    weather_info: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    is_selected: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    trip = relationship("Trip", back_populates="recommendations")
