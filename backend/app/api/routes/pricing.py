import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db, get_user_trip
from app.models.trip import Trip
from app.schemas.common import APIResponse
from app.schemas.pricing import CostBreakdownResponse, PriceValidationRequest, PriceValidationResponse
from app.services.cost_service import CostService
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/trips/{trip_id}", tags=["Pricing & Cost"])


@router.get("/cost", response_model=APIResponse[CostBreakdownResponse])
async def get_trip_cost(
    trip_id: uuid.UUID,
    itinerary_id: Optional[uuid.UUID] = Query(None),
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    cost_data = await CostService.calculate_trip_cost(
        db=db,
        trip_id=trip.id,
        itinerary_id=itinerary_id
    )
    return APIResponse.ok(
        data=cost_data,
        message="Authoritative total trip cost calculated."
    )


@router.post("/validate-price", response_model=APIResponse[PriceValidationResponse])
async def validate_price(
    trip_id: uuid.UUID,
    req: PriceValidationRequest,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    pricing_svc = PricingService()
    validation = await pricing_svc.validate_component_price(
        category=req.item_category,
        item_id=req.item_id,
        expected_price=req.expected_price,
        currency=req.currency
    )
    return APIResponse.ok(
        data=validation,
        message=validation.message
    )
