import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CostBreakdownResponse(BaseModel):
    trip_id: uuid.UUID
    flight_cost: float
    hotel_cost: float
    activity_cost: float
    transfer_cost: float
    taxes: float
    fees: float
    discounts: float
    total: float
    currency: str = "INR"
    selected_components: dict = Field(default_factory=dict)
    calculated_at: datetime


class PriceValidationRequest(BaseModel):
    item_category: str
    item_id: str
    expected_price: float
    currency: str = "INR"


class PriceValidationResponse(BaseModel):
    item_id: str
    category: str
    provider: str
    quoted_price: float
    current_price: float
    currency: str
    is_valid: bool
    is_stale: bool
    price_changed: bool
    available: bool
    message: str
    checked_at: datetime
