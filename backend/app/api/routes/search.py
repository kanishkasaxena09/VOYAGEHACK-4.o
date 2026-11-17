import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.search_agent import SearchAgent
from app.api.deps import get_current_user, get_db, get_user_trip
from app.models.trip import Trip
from app.schemas.common import APIResponse
from app.schemas.search import (
    SearchActivityRequest,
    SearchAllResponse,
    SearchFlightRequest,
    SearchHotelRequest,
    SearchResultResponse,
    SearchTransferRequest,
)

router = APIRouter(prefix="/trips/{trip_id}/search", tags=["Search"])


@router.post("/flights", response_model=APIResponse[List[SearchResultResponse]])
async def search_flights(
    trip_id: uuid.UUID,
    req: Optional[SearchFlightRequest] = None,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = SearchAgent()
    results = await agent.search_flights(db, trip, req)
    return APIResponse.ok(data=results, message="Flight search completed.")


@router.post("/hotels", response_model=APIResponse[List[SearchResultResponse]])
async def search_hotels(
    trip_id: uuid.UUID,
    req: Optional[SearchHotelRequest] = None,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = SearchAgent()
    results = await agent.search_hotels(db, trip, req)
    return APIResponse.ok(data=results, message="Hotel search completed.")


@router.post("/activities", response_model=APIResponse[List[SearchResultResponse]])
async def search_activities(
    trip_id: uuid.UUID,
    req: Optional[SearchActivityRequest] = None,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = SearchAgent()
    results = await agent.search_activities(db, trip, req)
    return APIResponse.ok(data=results, message="Activity search completed.")


@router.post("/transfers", response_model=APIResponse[List[SearchResultResponse]])
async def search_transfers(
    trip_id: uuid.UUID,
    req: Optional[SearchTransferRequest] = None,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = SearchAgent()
    results = await agent.search_transfers(db, trip, req)
    return APIResponse.ok(data=results, message="Transfer search completed.")


@router.post("/all", response_model=APIResponse[SearchAllResponse])
async def search_all(
    trip_id: uuid.UUID,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = SearchAgent()
    results = await agent.search_all(db, trip)
    return APIResponse.ok(data=results, message="Comprehensive search completed.")
