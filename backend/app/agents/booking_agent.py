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
from app.core.logging import logger
from app.models.booking import Booking, BookingItem, BookingStatus
from app.models.itinerary import Itinerary
from app.models.pending_action import ActionStatus, ActionType, PendingAction
from app.models.search import SearchResult
from app.models.trip import Trip, TripStatus
from app.providers.mock_booking import MockBookingProvider
from app.schemas.booking import BookingResponse
from app.services.audit_service import AuditService
from app.services.confirmation_service import ConfirmationService
from app.services.cost_service import CostService
from app.services.pricing_service import PricingService


class BookingAgent:
    def __init__(self):
        self.booking_provider = MockBookingProvider()
        self.pricing_service = PricingService()

    async def prepare_booking(
        self,
        db: AsyncSession,
        trip: Trip,
        itinerary_id: Optional[uuid.UUID] = None,
        idempotency_key: Optional[str] = None
    ) -> PendingAction:
        """Prepares a booking and creates a PendingAction awaiting human confirmation."""
        # 1. Calculate authoritative total cost
        cost_breakdown = await CostService.calculate_trip_cost(db, trip.id, itinerary_id)

        # 2. Re-validate inventory & price
        # Retrieve search results to ensure no items are stale or sold out
        sr_stmt = select(SearchResult).where(SearchResult.trip_id == trip.id, SearchResult.available == True)
        sr_res = await db.execute(sr_stmt)
        search_items = sr_res.scalars().all()

        components_to_book = []
        if search_items:
            for itm in search_items:
                components_to_book.append({
                    "category": itm.category,
                    "provider": itm.provider,
                    "external_id": itm.external_id,
                    "title": itm.title,
                    "price": itm.price,
                    "currency": itm.currency,
                    "cancellation_policy": itm.cancellation_policy,
                    "details": itm.details
                })
        else:
            # Construct standard components from balanced plan
            components_to_book = [
                {
                    "category": "FLIGHT",
                    "provider": "MockAirlines",
                    "external_id": "FL-GOA-101",
                    "title": "IndiGo 6E-2041 (Delhi to Goa Roundtrip)",
                    "price": cost_breakdown.flight_cost,
                    "currency": "INR",
                    "cancellation_policy": "Refundable up to 24h prior minus ₹1,500 penalty."
                },
                {
                    "category": "HOTEL",
                    "provider": "MockHotels",
                    "external_id": "HT-GOA-BALANCED",
                    "title": "Candolim Beach Resort & Spa (4 Nights)",
                    "price": cost_breakdown.hotel_cost,
                    "currency": "INR",
                    "cancellation_policy": "Free cancellation up to 48 hours before check-in."
                },
                {
                    "category": "ACTIVITY",
                    "provider": "MockActivities",
                    "external_id": "ACT-GOA-1",
                    "title": "Mandovi River Sunset Cruise & Spice Tour",
                    "price": cost_breakdown.activity_cost,
                    "currency": "INR",
                    "cancellation_policy": "Full refund up to 24h prior."
                },
                {
                    "category": "TRANSFER",
                    "provider": "MockTransfers",
                    "external_id": "TR-GOA-1",
                    "title": "Private Airport Return Transfer",
                    "price": cost_breakdown.transfer_cost,
                    "currency": "INR",
                    "cancellation_policy": "Free cancellation up to 6 hours prior."
                }
            ]

        # 3. Create PendingAction requiring human confirmation
        action_details = {
            "trip_id": str(trip.id),
            "itinerary_id": str(itinerary_id) if itinerary_id else None,
            "components": components_to_book,
            "cost_breakdown": cost_breakdown.model_dump(mode="json")
        }

        key = idempotency_key or f"book-{trip.id}-{uuid.uuid4().hex[:8]}"

        pending_action = await ConfirmationService.create_pending_action(
            db=db,
            trip_id=trip.id,
            user_id=trip.user_id,
            action_type=ActionType.BOOK_TRIP,
            estimated_amount=cost_breakdown.total,
            currency=cost_breakdown.currency,
            details=action_details,
            idempotency_key=key,
            expiry_minutes=20
        )

        trip.status = TripStatus.READY_TO_BOOK
        await db.flush()

        return pending_action

    async def confirm_and_execute_booking(
        self,
        db: AsyncSession,
        trip: Trip,
        pending_action_id: uuid.UUID,
        idempotency_key: str
    ) -> BookingResponse:
        """Executes booking with provider after validating pending action and confirmation gate."""
        # Check idempotency directly on existing booking
        existing_b_stmt = select(Booking).where(Booking.idempotency_key == idempotency_key)
        res_existing = await db.execute(existing_b_stmt)
        existing_booking = res_existing.scalars().first()
        if existing_booking:
            # Return idempotent response
            return await self._get_booking_response(db, existing_booking.id)

        # 1. Human-in-the-loop Gate Validation
        pending_action = await ConfirmationService.get_and_validate_for_execution(
            db=db,
            pending_action_id=pending_action_id,
            user_id=trip.user_id,
            idempotency_key=idempotency_key
        )

        components = pending_action.details.get("components", [])

        # 2. Provider API Execution
        try:
            provider_result = await self.booking_provider.create_booking(
                trip_id=str(trip.id),
                user_id=str(trip.user_id),
                components=components,
                idempotency_key=idempotency_key
            )
        except Exception as e:
            await ConfirmationService.mark_failed(db, pending_action, str(e))
            raise ValidationException(f"Booking execution failed at provider: {e}")

        # 3. Store Booking Record
        booking = Booking(
            trip_id=trip.id,
            user_id=trip.user_id,
            booking_reference=provider_result["booking_reference"],
            status=BookingStatus.CONFIRMED,
            total_amount=provider_result["total_amount"],
            currency=provider_result["currency"],
            idempotency_key=idempotency_key,
            cancellation_policy=provider_result.get("cancellation_policy"),
            penalty_fee=provider_result.get("penalty_fee", 0.0),
            refund_amount=0.0,
            voucher_data=provider_result.get("voucher_data", {})
        )
        db.add(booking)
        await db.flush()

        # 4. Store Booking Items
        for item_data in provider_result.get("items", []):
            b_item = BookingItem(
                booking_id=booking.id,
                category=item_data["category"],
                provider=item_data["provider"],
                provider_booking_id=item_data["provider_booking_id"],
                title=item_data["title"],
                price=item_data["price"],
                currency=item_data["currency"],
                status=item_data["status"],
                cancellation_policy=item_data.get("cancellation_policy"),
                details=item_data.get("details", {})
            )
            db.add(b_item)

        # 5. Transition Trip & PendingAction states
        trip.status = TripStatus.BOOKED
        await ConfirmationService.mark_completed(
            db=db,
            action=pending_action,
            result_details={"booking_reference": booking.booking_reference, "booking_id": str(booking.id)}
        )

        await AuditService.log_action(
            db=db,
            action="BOOKING_CONFIRMED",
            actor="USER",
            trip_id=trip.id,
            user_id=trip.user_id,
            input_data={"pending_action_id": str(pending_action_id), "idempotency_key": idempotency_key},
            result={"booking_reference": booking.booking_reference, "total_amount": booking.total_amount}
        )

        await db.flush()
        return await self._get_booking_response(db, booking.id)

    async def _get_booking_response(self, db: AsyncSession, booking_id: uuid.UUID) -> BookingResponse:
        stmt = select(Booking).where(Booking.id == booking_id).options(selectinload(Booking.items))
        res = await db.execute(stmt)
        b = res.scalars().first()
        if not b:
            raise ResourceNotFoundException("Booking", booking_id)
        return BookingResponse.model_validate(b)
