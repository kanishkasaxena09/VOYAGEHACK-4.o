import uuid
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SearchFlightRequest(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    passengers: int = 1
    cabin_class: Optional[str] = "economy"
    nonstop_only: bool = False


class SearchHotelRequest(BaseModel):
    city: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    guests: int = 2
    category: Optional[str] = None
    max_price_per_night: Optional[float] = None


class SearchActivityRequest(BaseModel):
    city: Optional[str] = None
    category: Optional[str] = None
    date: Optional[date] = None
    participants: int = 2


class SearchTransferRequest(BaseModel):
    city: Optional[str] = None
    passengers: int = 2
    vehicle_type: Optional[str] = None


class SearchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    category: str
    provider: str
    external_id: str
    title: str
    price: float
    currency: str
    available: bool
    cancellation_policy: Optional[str] = None
    penalty_fee: Optional[float] = 0.0
    details: dict = Field(default_factory=dict)
    checked_at: datetime
    is_stale: bool = False


class SearchAllResponse(BaseModel):
    trip_id: uuid.UUID
    flights: List[SearchResultResponse] = Field(default_factory=list)
    hotels: List[SearchResultResponse] = Field(default_factory=list)
    activities: List[SearchResultResponse] = Field(default_factory=list)
    transfers: List[SearchResultResponse] = Field(default_factory=list)
