import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.destination_agent import DestinationAgent
from app.api.deps import get_current_user, get_db, get_user_trip
from app.models.destination import DestinationRecommendation
from app.models.trip import Trip
from app.schemas.common import APIResponse
from app.schemas.destination import DestinationDiscoverRequest, DestinationRecommendationResponse

router = APIRouter(prefix="/trips/{trip_id}/destinations", tags=["Destinations"])


@router.post("/discover", response_model=APIResponse[List[DestinationRecommendationResponse]])
async def discover_destinations(
    trip_id: uuid.UUID,
    req: DestinationDiscoverRequest = DestinationDiscoverRequest(),
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    recommendations = await DestinationAgent.discover_destinations(
        trip=trip,
        max_recommendations=req.max_recommendations
    )

    # Persist in DB
    for rec in recommendations:
        rec_model = DestinationRecommendation(
            trip_id=trip.id,
            destination=rec.destination,
            fit_score=rec.fit_score,
            why_it_fits=rec.why_it_fits,
            tradeoffs=rec.tradeoffs,
            estimated_cost=rec.estimated_cost,
            currency=rec.currency,
            weather_info=rec.weather_info,
            is_selected=rec.is_selected
        )
        db.add(rec_model)
    await db.flush()

    return APIResponse.ok(
        data=recommendations,
        message="Destinations discovered and ranked."
    )
