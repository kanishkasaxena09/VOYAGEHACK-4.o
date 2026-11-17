import uuid
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TravellerCreate(BaseModel):
    first_name: str
    last_name: str
    age: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    passport_number: Optional[str] = None
    special_requests: Optional[str] = None


class TravellerResponse(TravellerCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID


class PreferenceBase(BaseModel):
    hotel_category: Optional[str] = None
    preferred_airline: Optional[str] = None
    cabin_class: Optional[str] = "economy"
    nonstop_required: bool = False
    max_flight_duration_minutes: Optional[int] = None
    food_preferences: List[str] = Field(default_factory=list)
    activity_preferences: List[str] = Field(default_factory=list)
    pace: Optional[str] = "relaxed"
    accessibility_requirements: List[str] = Field(default_factory=list)
    things_to_avoid: List[str] = Field(default_factory=list)
    extra_preferences: Optional[dict] = Field(default_factory=dict)


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceResponse(PreferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID


class ConstraintCreate(BaseModel):
    constraint_type: str
    value: str
    severity: str = "HARD"  # HARD or SOFT
    description: Optional[str] = None


class ConstraintResponse(ConstraintCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    created_at: datetime


class TripCreate(BaseModel):
    title: Optional[str] = "My Upcoming Trip"
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    number_of_travellers: int = 1
    budget_amount: Optional[float] = None
    budget_currency: str = "INR"
    purpose: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    pace: Optional[str] = "relaxed"
    preferences: Optional[PreferenceCreate] = None
    constraints: Optional[List[ConstraintCreate]] = None


class TripUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    number_of_travellers: Optional[int] = None
    budget_amount: Optional[float] = None
    budget_currency: Optional[str] = None
    purpose: Optional[str] = None
    interests: Optional[List[str]] = None
    pace: Optional[str] = None


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    status: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    number_of_travellers: int
    budget_amount: Optional[float] = None
    budget_currency: str
    purpose: Optional[str] = None
    interests: List[str]
    pace: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    preferences: Optional[PreferenceResponse] = None
    constraints: List[ConstraintResponse] = Field(default_factory=list)
    travellers: List[TravellerResponse] = Field(default_factory=list)


class TravelIntent(BaseModel):
    """Structured LLM extracted travel intent."""
    origin: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_days: Optional[int] = None
    number_of_travellers: Optional[int] = None
    budget: Optional[float] = None
    currency: Optional[str] = "INR"
    interests: List[str] = Field(default_factory=list)
    pace: Optional[str] = None
    hotel_preference: Optional[str] = None
    flight_preference: Optional[str] = None
    food_preferences: List[str] = Field(default_factory=list)
    hard_constraints: List[str] = Field(default_factory=list)
    soft_preferences: List[str] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
