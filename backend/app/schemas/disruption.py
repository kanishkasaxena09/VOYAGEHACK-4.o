import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DisruptionAlternativeOption(BaseModel):
    alternative_id: str
    provider: str
    description: str
    price_difference: float = 0.0
    refund_amount: float = 0.0
    additional_fee: float = 0.0
    currency: str = "INR"
    details: Optional[dict] = Field(default_factory=dict)


class DisruptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trip_id: uuid.UUID
    disruption_type: str
    target_type: str
    reference_id: str
    severity: str
    reason: str
    status: str
    impact_summary: Optional[str] = None
    original_data: dict
    alternative_options: List[dict]
    selected_option: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class DisruptionConfirmRequest(BaseModel):
    alternative_id: str
    idempotency_key: str
