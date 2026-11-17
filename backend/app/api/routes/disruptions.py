import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.disruption_agent import DisruptionAgent
from app.api.deps import get_current_user, get_db, get_user_trip
from app.models.trip import Trip
from app.schemas.common import APIResponse
from app.schemas.disruption import DisruptionConfirmRequest, DisruptionResponse

router = APIRouter(prefix="/trips/{trip_id}/disruptions", tags=["Disruptions"])


@router.get("", response_model=APIResponse[List[DisruptionResponse]])
async def check_disruptions(
    trip_id: uuid.UUID,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = DisruptionAgent()
    disruptions = await agent.check_and_detect_disruptions(db, trip.id)
    return APIResponse.ok(
        data=disruptions,
        message="Active disruptions retrieved."
    )


@router.post("/{disruption_id}/options", response_model=APIResponse[dict])
async def get_disruption_options(
    trip_id: uuid.UUID,
    disruption_id: uuid.UUID,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = DisruptionAgent()
    options = await agent.get_disruption_options(db, trip.id, disruption_id)
    return APIResponse.ok(
        data=options,
        message="Alternative recovery options loaded."
    )


@router.post("/{disruption_id}/confirm", response_model=APIResponse[dict])
async def confirm_disruption_resolution(
    trip_id: uuid.UUID,
    disruption_id: uuid.UUID,
    req: DisruptionConfirmRequest,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = DisruptionAgent()
    result = await agent.confirm_disruption_resolution(
        db=db,
        trip=trip,
        disruption_id=disruption_id,
        alternative_id=req.alternative_id,
        idempotency_key=req.idempotency_key
    )
    return APIResponse.ok(
        data=result,
        message="Disruption successfully resolved."
    )
