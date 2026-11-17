import uuid
from datetime import date as dt_date, datetime as dt_datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ItineraryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    day_number: int
    date: Optional[dt_date] = None
    location: str
    morning: Optional[str] = None
    afternoon: Optional[str] = None
    evening: Optional[str] = None
    activities: List[dict] = Field(default_factory=list)
    hotel: Optional[dict] = Field(default_factory=dict)
    transport: Optional[dict] = Field(default_factory=dict)
    estimated_cost: float
    travel_time_minutes: Optional[int] = 0
    notes: Optional[str] = None


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    tier: str  # Budget, Balanced, Premium
    title: str
    total_estimated_cost: float
    currency: str
    is_selected: bool
    highlights: List[str]
    items: List[ItineraryItemResponse] = Field(default_factory=list)


class ItineraryGenerateRequest(BaseModel):
    tiers: Optional[List[str]] = Field(default=["Budget", "Balanced", "Premium"])
    destination: Optional[str] = None


class ItinerarySelectRequest(BaseModel):
    itinerary_id: uuid.UUID


class ItineraryReplanRequest(BaseModel):
    target_budget: Optional[float] = None
    change_flight: bool = False
    change_hotel: bool = False
    change_activities: bool = False
    new_dates: Optional[tuple[dt_date, dt_date]] = None
    removed_activity_ids: Optional[List[str]] = None
    explanation: Optional[str] = None
