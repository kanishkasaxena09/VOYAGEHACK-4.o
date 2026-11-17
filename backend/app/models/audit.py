import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="SET NULL"), index=True, nullable=True
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False
    )
    actor: Mapped[str] = mapped_column(
        String(50), default="USER", nullable=False  # USER, AGENT, SYSTEM
    )
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON, default=dict, nullable=True
    )
    result: Mapped[Optional[dict]] = mapped_column(
        JSON, default=dict, nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User", back_populates="audit_logs")
    trip = relationship("Trip", back_populates="audit_logs")
