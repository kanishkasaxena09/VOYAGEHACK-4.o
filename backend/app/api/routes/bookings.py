import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.agents.booking_agent import BookingAgent
from app.agents.trip_management_agent import TripManagementAgent
from app.api.deps import get_current_user, get_db, get_user_trip
from app.core.exceptions import ResourceNotFoundException
from app.models.booking import Booking
from app.models.trip import Trip
from app.models.user import User
from app.schemas.booking import (
    BookingConfirmRequest,
    BookingPrepareRequest,
    BookingResponse,
    CancelConfirmRequest,
    CancelPrepareRequest,
    ModifyConfirmRequest,
    ModifyPrepareRequest,
    PendingActionResponse,
)
from app.schemas.common import APIResponse

router = APIRouter(tags=["Bookings & Trip Management"])


@router.post("/trips/{trip_id}/booking/prepare", response_model=APIResponse[PendingActionResponse])
async def prepare_booking(
    trip_id: uuid.UUID,
    req: BookingPrepareRequest = BookingPrepareRequest(),
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = BookingAgent()
    pending = await agent.prepare_booking(
        db=db,
        trip=trip,
        itinerary_id=req.itinerary_id,
        idempotency_key=req.idempotency_key
    )
    return APIResponse.ok(
        data=PendingActionResponse.model_validate(pending),
        message="Booking prepared. Confirmation required before execution."
    )


@router.post("/trips/{trip_id}/booking/confirm", response_model=APIResponse[BookingResponse])
async def confirm_booking(
    trip_id: uuid.UUID,
    req: BookingConfirmRequest,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    agent = BookingAgent()
    booking = await agent.confirm_and_execute_booking(
        db=db,
        trip=trip,
        pending_action_id=req.pending_action_id,
        idempotency_key=req.idempotency_key
    )
    return APIResponse.ok(
        data=booking,
        message="Booking confirmed and vouchers generated."
    )


@router.get("/trips/{trip_id}/bookings", response_model=APIResponse[List[BookingResponse]])
async def get_trip_bookings(
    trip_id: uuid.UUID,
    trip: Trip = Depends(get_user_trip),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Booking).where(Booking.trip_id == trip.id).options(selectinload(Booking.items))
    res = await db.execute(stmt)
    bookings = res.scalars().all()
    return APIResponse.ok(
        data=[BookingResponse.model_validate(b) for b in bookings],
        message="Bookings retrieved."
    )


@router.get("/trips/{trip_id}/vouchers", response_model=APIResponse[List[dict]])
async def get_trip_vouchers(
    trip_id: uuid.UUID,
    trip: Trip = Depends(get_user_trip),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    agent = TripManagementAgent()
    vouchers = await agent.get_trip_vouchers(db, trip.id, user.id)
    return APIResponse.ok(
        data=vouchers,
        message="Vouchers retrieved."
    )


# --- Booking Modification & Cancellation ---

@router.post("/bookings/{booking_id}/cancel/prepare", response_model=APIResponse[PendingActionResponse])
async def prepare_cancellation(
    booking_id: uuid.UUID,
    req: CancelPrepareRequest = CancelPrepareRequest(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    agent = TripManagementAgent()
    pending = await agent.prepare_cancellation(
        db=db,
        booking_id=booking_id,
        user_id=user.id,
        reason=req.reason
    )
    return APIResponse.ok(
        data=PendingActionResponse.model_validate(pending),
        message="Cancellation impact calculated. Confirmation required."
    )


@router.post("/bookings/{booking_id}/cancel/confirm", response_model=APIResponse[BookingResponse])
async def confirm_cancellation(
    booking_id: uuid.UUID,
    req: CancelConfirmRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    agent = TripManagementAgent()
    booking = await agent.confirm_cancellation(
        db=db,
        booking_id=booking_id,
        user_id=user.id,
        pending_action_id=req.pending_action_id,
        idempotency_key=req.idempotency_key
    )
    return APIResponse.ok(
        data=booking,
        message="Booking cancellation confirmed and refund scheduled."
    )


@router.post("/bookings/{booking_id}/modify/prepare", response_model=APIResponse[PendingActionResponse])
async def prepare_modification(
    booking_id: uuid.UUID,
    req: ModifyPrepareRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    agent = TripManagementAgent()
    pending = await agent.prepare_modification(
        db=db,
        booking_id=booking_id,
        user_id=user.id,
        modify_category=req.modify_category,
        new_option_id=req.new_option_id,
        reason=req.reason
    )
    return APIResponse.ok(
        data=PendingActionResponse.model_validate(pending),
        message="Modification fees calculated. Confirmation required."
    )


@router.post("/bookings/{booking_id}/modify/confirm", response_model=APIResponse[BookingResponse])
async def confirm_modification(
    booking_id: uuid.UUID,
    req: ModifyConfirmRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    agent = TripManagementAgent()
    booking = await agent.confirm_modification(
        db=db,
        booking_id=booking_id,
        user_id=user.id,
        pending_action_id=req.pending_action_id,
        idempotency_key=req.idempotency_key
    )
    return APIResponse.ok(
        data=booking,
        message="Booking modification successfully confirmed."
    )
