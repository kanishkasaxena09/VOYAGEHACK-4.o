import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DestinationDiscoverRequest(BaseModel):
    max_recommendations: int = 3
    override_budget: Optional[float] = None
    override_interests: Optional[List[str]] = None


class DestinationRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[uuid.UUID] = None
    destination: str
    fit_score: int
    why_it_fits: List[str]
    tradeoffs: List[str] = Field(default_factory=list)
    estimated_cost: float
    currency: str = "INR"
    weather_info: Optional[str] = None
    is_selected: bool = False
