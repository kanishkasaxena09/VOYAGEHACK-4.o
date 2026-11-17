import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import (
    ConfirmationRequiredException,
    DuplicateActionException,
    ResourceNotFoundException,
    ValidationException,
)
from app.models.booking import Booking, BookingItem, BookingStatus
from app.models.pending_action import ActionStatus, ActionType, PendingAction
from app.models.trip import Trip, TripStatus
from app.providers.mock_booking import MockBookingProvider
from app.schemas.booking import BookingResponse
from app.services.audit_service import AuditService
from app.services.confirmation_service import ConfirmationService


class TripManagementAgent:
    def __init__(self):
        self.booking_provider = MockBookingProvider()

    async def get_trip_vouchers(
        self,
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        stmt = (
            select(Booking)
            .where(Booking.trip_id == trip_id, Booking.user_id == user_id)
            .options(selectinload(Booking.items))
        )
        res = await db.execute(stmt)
        bookings = res.scalars().all()

        vouchers = []
        for b in bookings:
            vouchers.append({
                "booking_id": str(b.id),
                "booking_reference": b.booking_reference,
                "status": b.status,
                "voucher_data": b.voucher_data or {
                    "voucher_code": f"VOUCHER-{b.booking_reference}",
                    "issued_to_user": str(user_id)
                },
                "items": [
                    {
                        "category": itm.category,
                        "title": itm.title,
                        "pnr": itm.provider_booking_id,
                        "status": itm.status,
                        "check_in_time": itm.details.get("check_in_time", "14:00") if itm.category == "HOTEL" else None,
                        "departure_time": itm.details.get("departure_time") if itm.category == "FLIGHT" else None,
                        "cancellation_policy": itm.cancellation_policy
                    }
                    for itm in b.items
                ]
            })
        return vouchers

    async def prepare_cancellation(
        self,
        db: AsyncSession,
        booking_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = "User requested cancellation"
    ) -> PendingAction:
        """Calculates penalty and refund before asking human confirmation."""
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id, Booking.user_id == user_id)
            .options(selectinload(Booking.items))
        )
        res = await db.execute(stmt)
        booking = res.scalars().first()
        if not booking:
            raise ResourceNotFoundException("Booking", booking_id)

        if booking.status == BookingStatus.CANCELLED:
            raise ValidationException("Booking is already cancelled.")

        # Calculate penalty and expected refund
        penalty_fee = booking.penalty_fee if (booking.penalty_fee and booking.penalty_fee > 0) else 4500.0
        expected_refund = max(0.0, booking.total_amount - penalty_fee)

        action_details = {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "total_paid": booking.total_amount,
            "penalty_fee": penalty_fee,
            "expected_refund": expected_refund,
            "currency": booking.currency,
            "policy": "Non-refundable provider service taxes and cancellation penalty deducted.",
            "reason": reason
        }

        pending = await ConfirmationService.create_pending_action(
            db=db,
            trip_id=booking.trip_id,
            user_id=user_id,
            action_type=ActionType.CANCEL_BOOKING,
            estimated_amount=expected_refund,
            currency=booking.currency,
            details=action_details,
            idempotency_key=f"cancel-{booking.id}-{uuid.uuid4().hex[:6]}"
        )

        return pending

    async def confirm_cancellation(
        self,
        db: AsyncSession,
        booking_id: uuid.UUID,
        user_id: uuid.UUID,
        pending_action_id: uuid.UUID,
        idempotency_key: str
    ) -> BookingResponse:
        """Executes cancellation after human confirmation gate."""
        stmt = select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id).options(selectinload(Booking.items))
        res = await db.execute(stmt)
        booking = res.scalars().first()
        if not booking:
            raise ResourceNotFoundException("Booking", booking_id)

        if booking.status == BookingStatus.CANCELLED:
            return BookingResponse.model_validate(booking)

        pending_action = await ConfirmationService.get_and_validate_for_execution(
            db=db,
            pending_action_id=pending_action_id,
            user_id=user_id,
            idempotency_key=idempotency_key
        )

        # Provider cancellation call
        provider_res = await self.booking_provider.cancel_booking(
            booking_reference=booking.booking_reference,
            reason=pending_action.details.get("reason")
        )

        penalty = pending_action.details.get("penalty_fee", 4500.0)
        refund = pending_action.details.get("expected_refund", booking.total_amount - penalty)

        booking.status = BookingStatus.CANCELLED
        booking.penalty_fee = penalty
        booking.refund_amount = refund

        for item in booking.items:
            item.status = "CANCELLED"

        # Update Trip status
        trip_stmt = select(Trip).where(Trip.id == booking.trip_id)
        t_res = await db.execute(trip_stmt)
        trip = t_res.scalars().first()
        if trip:
            trip.status = TripStatus.CANCELLED

        await ConfirmationService.mark_completed(
            db=db,
            action=pending_action,
            result_details={"status": "CANCELLED", "refund_amount": refund}
        )

        await AuditService.log_action(
            db=db,
            action="BOOKING_CANCELLED",
            actor="USER",
            trip_id=booking.trip_id,
            user_id=user_id,
            input_data={"booking_id": str(booking_id), "pending_action_id": str(pending_action_id)},
            result={"penalty_fee": penalty, "refund_amount": refund}
        )

        await db.flush()
        return BookingResponse.model_validate(booking)

    async def prepare_modification(
        self,
        db: AsyncSession,
        booking_id: uuid.UUID,
        user_id: uuid.UUID,
        modify_category: str,
        new_option_id: str,
        reason: Optional[str] = "User requested modification"
    ) -> PendingAction:
        """Prepares a paid modification with diff calculation before confirmation."""
        stmt = (
            select(Booking)
            .where(Booking.id == booking_id, Booking.user_id == user_id)
            .options(selectinload(Booking.items))
        )
        res = await db.execute(stmt)
        booking = res.scalars().first()
        if not booking:
            raise ResourceNotFoundException("Booking", booking_id)

        modification_fee = 1000.0
        fare_difference = 1500.0
        total_additional_cost = modification_fee + fare_difference

        action_details = {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "modify_category": modify_category,
            "new_option_id": new_option_id,
            "modification_fee": modification_fee,
            "fare_difference": fare_difference,
            "total_additional_cost": total_additional_cost,
            "currency": booking.currency,
            "reason": reason
        }

        pending = await ConfirmationService.create_pending_action(
            db=db,
            trip_id=booking.trip_id,
            user_id=user_id,
            action_type=ActionType.MODIFY_BOOKING,
            estimated_amount=total_additional_cost,
            currency=booking.currency,
            details=action_details,
            idempotency_key=f"mod-{booking.id}-{uuid.uuid4().hex[:6]}"
        )

        return pending

    async def confirm_modification(
        self,
        db: AsyncSession,
        booking_id: uuid.UUID,
        user_id: uuid.UUID,
        pending_action_id: uuid.UUID,
        idempotency_key: str
    ) -> BookingResponse:
        """Executes paid modification after human confirmation."""
        stmt = select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id).options(selectinload(Booking.items))
        res = await db.execute(stmt)
        booking = res.scalars().first()
        if not booking:
            raise ResourceNotFoundException("Booking", booking_id)

        pending_action = await ConfirmationService.get_and_validate_for_execution(
            db=db,
            pending_action_id=pending_action_id,
            user_id=user_id,
            idempotency_key=idempotency_key
        )

        # Provider call
        provider_res = await self.booking_provider.modify_booking(
            booking_reference=booking.booking_reference,
            modification_details=pending_action.details
        )

        additional = pending_action.details.get("total_additional_cost", 2500.0)
        booking.total_amount += additional
        booking.status = BookingStatus.MODIFIED

        await ConfirmationService.mark_completed(
            db=db,
            action=pending_action,
            result_details={"status": "MODIFIED", "additional_amount": additional}
        )

        await AuditService.log_action(
            db=db,
            action="BOOKING_MODIFIED",
            actor="USER",
            trip_id=booking.trip_id,
            user_id=user_id,
            input_data={"booking_id": str(booking_id), "pending_action_id": str(pending_action_id)},
            result={"new_total": booking.total_amount}
        )

        await db.flush()
        return BookingResponse.model_validate(booking)
