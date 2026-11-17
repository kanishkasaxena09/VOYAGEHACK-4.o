import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PendingActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    user_id: uuid.UUID
    action_type: str
    status: str
    idempotency_key: str
    estimated_amount: float
    currency: str
    expires_at: datetime
    details: dict
    created_at: datetime


class BookingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    provider: str
    provider_booking_id: str
    title: str
    price: float
    currency: str
    status: str
    cancellation_policy: Optional[str] = None
    details: dict


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    user_id: uuid.UUID
    booking_reference: str
    status: str
    total_amount: float
    currency: str
    idempotency_key: Optional[str] = None
    cancellation_policy: Optional[str] = None
    penalty_fee: Optional[float] = 0.0
    refund_amount: Optional[float] = 0.0
    voucher_data: Optional[dict] = None
    items: List[BookingItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BookingPrepareRequest(BaseModel):
    itinerary_id: Optional[uuid.UUID] = None
    idempotency_key: Optional[str] = None


class BookingConfirmRequest(BaseModel):
    pending_action_id: uuid.UUID
    idempotency_key: str = Field(..., description="Unique client key preventing double-booking")


class CancelPrepareRequest(BaseModel):
    reason: Optional[str] = "User requested cancellation"


class CancelConfirmRequest(BaseModel):
    pending_action_id: uuid.UUID
    idempotency_key: str


class ModifyPrepareRequest(BaseModel):
    modify_category: str  # FLIGHT, HOTEL
    new_option_id: str
    reason: Optional[str] = "User requested modification"


class ModifyConfirmRequest(BaseModel):
    pending_action_id: uuid.UUID
    idempotency_key: str
