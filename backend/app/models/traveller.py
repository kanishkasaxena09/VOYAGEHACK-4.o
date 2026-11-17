import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, GUID


class Traveller(Base):
    __tablename__ = "travellers"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("trips.id", ondelete="CASCADE"), index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    age: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    passport_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    special_requests: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    trip = relationship("Trip", back_populates="travellers")
