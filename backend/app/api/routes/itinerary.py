import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.agents.itinerary_agent import ItineraryAgent
from app.api.deps import get_current_user, get_db, get_user_trip
from app.core.exceptions import ResourceNotFoundException
from app.models.itinerary import Itinerary, ItineraryItem
from app.models.trip import Trip, TripStatus
from app.schemas.common import APIResponse
from app.schemas.itinerary import (
    ItineraryGenerateRequest,
    ItineraryReplanRequest,
    ItineraryResponse,
    ItinerarySelectRequest,
)
from app.services.replanning_service import ReplanningService

router = APIRouter(prefix="/trips/{trip_id}/itinerary", tags=["Itinerary"])


@router.post("/generate", response_model=APIResponse[List[ItineraryResponse]])
async def generate_itineraries(
    trip_id: uuid.UUID,
    req: ItineraryGenerateRequest = ItineraryGenerateRequest(),
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    variants = ItineraryAgent.generate_itineraries(trip, destination=req.destination)
    saved_itineraries = []

    for v in variants:
        itin_obj = Itinerary(
            trip_id=trip.id,
            tier=v["tier"],
            title=v["title"],
            total_estimated_cost=v["total_estimated_cost"],
            currency=v["currency"],
            is_selected=(v["tier"] == "Balanced"),
            highlights=v["highlights"]
        )
        db.add(itin_obj)
        await db.flush()

        for itm in v["items"]:
            item_obj = ItineraryItem(
                itinerary_id=itin_obj.id,
                day_number=itm["day_number"],
                date=itm["date"],
                location=itm["location"],
                morning=itm["morning"],
                afternoon=itm["afternoon"],
                evening=itm["evening"],
                activities=itm["activities"],
                hotel=itm["hotel"],
                transport=itm["transport"],
                estimated_cost=itm["estimated_cost"],
                travel_time_minutes=itm.get("travel_time_minutes", 45),
                notes=itm.get("notes")
            )
            db.add(item_obj)

        saved_itineraries.append(itin_obj)

    trip.status = TripStatus.PLANNING
    await db.flush()

    # Re-fetch with loaded items
    res_list = []
    for s in saved_itineraries:
        stmt = select(Itinerary).where(Itinerary.id == s.id).options(selectinload(Itinerary.items))
        res = await db.execute(stmt)
        res_list.append(res.scalars().first())

    return APIResponse.ok(
        data=[ItineraryResponse.model_validate(it) for it in res_list],
        message="Itinerary variants generated successfully."
    )


@router.get("", response_model=APIResponse[List[ItineraryResponse]])
async def get_trip_itineraries(
    trip_id: uuid.UUID,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Itinerary).where(Itinerary.trip_id == trip.id).options(selectinload(Itinerary.items))
    res = await db.execute(stmt)
    itineraries = res.scalars().all()

    return APIResponse.ok(
        data=[ItineraryResponse.model_validate(i) for i in itineraries],
        message="Itineraries retrieved."
    )


@router.patch("/select", response_model=APIResponse[ItineraryResponse])
async def select_itinerary(
    trip_id: uuid.UUID,
    req: ItinerarySelectRequest,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Itinerary).where(Itinerary.trip_id == trip.id).options(selectinload(Itinerary.items))
    res = await db.execute(stmt)
    itineraries = res.scalars().all()

    selected = None
    for itin in itineraries:
        if itin.id == req.itinerary_id:
            itin.is_selected = True
            selected = itin
        else:
            itin.is_selected = False

    if not selected:
        raise ResourceNotFoundException("Itinerary", req.itinerary_id)

    await db.flush()
    return APIResponse.ok(
        data=ItineraryResponse.model_validate(selected),
        message=f"Itinerary '{selected.title}' selected."
    )


@router.post("/replan", response_model=APIResponse[dict])
async def replan_itinerary(
    trip_id: uuid.UUID,
    req: ItineraryReplanRequest,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Itinerary).where(Itinerary.trip_id == trip.id, Itinerary.is_selected == True)
    res = await db.execute(stmt)
    itin = res.scalars().first()

    if not itin:
        stmt_any = select(Itinerary).where(Itinerary.trip_id == trip.id)
        res_any = await db.execute(stmt_any)
        itin = res_any.scalars().first()

    if not itin:
        raise ResourceNotFoundException("Itinerary for trip", trip_id)

    replanner = ReplanningService()
    replan_result = await replanner.replan_itinerary(
        db=db,
        trip=trip,
        itinerary_id=itin.id,
        target_budget=req.target_budget,
        change_flight=req.change_flight,
        change_hotel=req.change_hotel,
        change_activities=req.change_activities,
        new_dates=req.new_dates,
        removed_activity_ids=req.removed_activity_ids,
        explanation=req.explanation
    )

    return APIResponse.ok(
        data=replan_result,
        message="Partial replanning complete."
    )
