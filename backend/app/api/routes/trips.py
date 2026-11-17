import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db, get_user_trip
from app.models.trip import Trip
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.trip import TripCreate, TripResponse, TripUpdate
from app.services.trip_service import TripService

router = APIRouter(prefix="/trips", tags=["Trips"])


@router.post("", response_model=APIResponse[TripResponse], status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_in: TripCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    trip = await TripService.create_trip(db=db, user_id=user.id, trip_in=trip_in)
    full_trip = await TripService.get_user_trip(db, trip.id, user.id)
    return APIResponse.ok(
        data=TripResponse.model_validate(full_trip),
        message="Trip created successfully."
    )


@router.get("", response_model=APIResponse[List[TripResponse]])
async def list_trips(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    trips = await TripService.list_user_trips(db=db, user_id=user.id, limit=limit, offset=offset)
    return APIResponse.ok(
        data=[TripResponse.model_validate(t) for t in trips],
        message="Trips retrieved."
    )


@router.get("/{trip_id}", response_model=APIResponse[TripResponse])
async def get_trip(
    trip: Trip = Depends(get_user_trip)
):
    return APIResponse.ok(
        data=TripResponse.model_validate(trip),
        message="Trip retrieved."
    )


@router.patch("/{trip_id}", response_model=APIResponse[TripResponse])
async def update_trip(
    trip_id: uuid.UUID,
    trip_update: TripUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    trip = await TripService.update_trip(db=db, trip_id=trip_id, user_id=user.id, trip_update=trip_update)
    full_trip = await TripService.get_user_trip(db, trip.id, user.id)
    return APIResponse.ok(
        data=TripResponse.model_validate(full_trip),
        message="Trip updated."
    )


@router.delete("/{trip_id}", response_model=APIResponse[dict])
async def delete_trip(
    trip_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await TripService.delete_trip(db=db, trip_id=trip_id, user_id=user.id)
    return APIResponse.ok(
        data={"deleted_trip_id": str(trip_id)},
        message="Trip deleted."
    )
