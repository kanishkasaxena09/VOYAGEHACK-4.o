import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ResourceNotFoundException
from app.models.conversation import Conversation, ConversationMessage
from app.models.preference import ConstraintSeverity, TripConstraint, TripPreference
from app.models.trip import Trip, TripStatus
from app.schemas.trip import TravelIntent


class MemoryService:
    @classmethod
    async def get_trip_with_memory(
        cls,
        db: AsyncSession,
        trip_id: uuid.UUID
    ) -> Trip:
        stmt = (
            select(Trip)
            .where(Trip.id == trip_id)
            .options(
                selectinload(Trip.preferences),
                selectinload(Trip.constraints),
                selectinload(Trip.travellers),
                selectinload(Trip.conversations).selectinload(Conversation.messages),
                selectinload(Trip.recommendations),
                selectinload(Trip.itineraries),
                selectinload(Trip.search_results),
                selectinload(Trip.bookings)
            )
        )
        res = await db.execute(stmt)
        trip = res.scalars().first()
        if not trip:
            raise ResourceNotFoundException("Trip", trip_id)
        return trip

    @classmethod
    async def update_trip_memory_from_intent(
        cls,
        db: AsyncSession,
        trip: Trip,
        intent: TravelIntent
    ) -> Dict[str, Any]:
        """Non-destructive update of Trip Memory from extracted intent."""
        updated_fields: List[str] = []

        # 1. Update Core Trip fields only if provided
        if intent.destination and intent.destination != trip.destination:
            trip.destination = intent.destination
            updated_fields.append("destination")

        if intent.origin and intent.origin != trip.origin:
            trip.origin = intent.origin
            updated_fields.append("origin")

        if intent.start_date and intent.start_date != trip.start_date:
            trip.start_date = intent.start_date
            updated_fields.append("start_date")

        if intent.end_date and intent.end_date != trip.end_date:
            trip.end_date = intent.end_date
            updated_fields.append("end_date")

        if intent.duration_days and intent.duration_days != trip.duration_days:
            trip.duration_days = intent.duration_days
            updated_fields.append("duration_days")

        if intent.number_of_travellers and intent.number_of_travellers != trip.number_of_travellers:
            trip.number_of_travellers = intent.number_of_travellers
            updated_fields.append("number_of_travellers")

        if intent.budget and intent.budget != trip.budget_amount:
            trip.budget_amount = intent.budget
            updated_fields.append("budget_amount")

        if intent.currency and intent.currency != trip.budget_currency:
            trip.budget_currency = intent.currency

        if intent.pace and intent.pace != trip.pace:
            trip.pace = intent.pace
            updated_fields.append("pace")

        if intent.interests:
            merged_interests = list(set(trip.interests + intent.interests))
            if set(merged_interests) != set(trip.interests):
                trip.interests = merged_interests
                updated_fields.append("interests")

        # 2. Update Preferences
        if not trip.preferences:
            trip.preferences = TripPreference(
                trip_id=trip.id,
                hotel_category=intent.hotel_preference,
                preferred_airline=intent.flight_preference,
                food_preferences=intent.food_preferences or [],
                pace=intent.pace or trip.pace or "relaxed"
            )
            db.add(trip.preferences)
            updated_fields.append("preferences_created")
        else:
            if intent.hotel_preference:
                trip.preferences.hotel_category = intent.hotel_preference
                updated_fields.append("hotel_category")
            if intent.flight_preference:
                trip.preferences.preferred_airline = intent.flight_preference
                updated_fields.append("preferred_airline")
            if intent.food_preferences:
                merged_food = list(set(trip.preferences.food_preferences + intent.food_preferences))
                trip.preferences.food_preferences = merged_food
                updated_fields.append("food_preferences")

        # 3. Update Hard Constraints (Non-violable)
        if intent.hard_constraints:
            for hc in intent.hard_constraints:
                # Avoid duplicate constraints
                exists = any(c.value.lower() == hc.lower() for c in trip.constraints)
                if not exists:
                    constraint = TripConstraint(
                        trip_id=trip.id,
                        constraint_type="HARD_CONSTRAINT",
                        value=hc,
                        severity=ConstraintSeverity.HARD,
                        description=f"User hard constraint: {hc}"
                    )
                    db.add(constraint)
                    trip.constraints.append(constraint)
                    updated_fields.append(f"constraint:{hc}")

        # Update budget constraint if budget is set
        if trip.budget_amount:
            b_str = f"MAX_BUDGET={trip.budget_amount}"
            has_b = False
            for c in trip.constraints:
                if c.constraint_type == "MAX_BUDGET":
                    c.value = str(trip.budget_amount)
                    has_b = True
                    break
            if not has_b:
                c_obj = TripConstraint(
                    trip_id=trip.id,
                    constraint_type="MAX_BUDGET",
                    value=str(trip.budget_amount),
                    severity=ConstraintSeverity.HARD,
                    description=f"Maximum trip budget of {trip.budget_currency} {trip.budget_amount}"
                )
                db.add(c_obj)
                trip.constraints.append(c_obj)

        trip.updated_at = datetime.now(timezone.utc)
        await db.flush()

        return {
            "updated_fields": updated_fields,
            "current_state": {
                "destination": trip.destination,
                "origin": trip.origin,
                "dates": f"{trip.start_date} to {trip.end_date}" if trip.start_date else None,
                "duration_days": trip.duration_days,
                "travellers": trip.number_of_travellers,
                "budget": f"{trip.budget_currency} {trip.budget_amount}" if trip.budget_amount else None,
                "interests": trip.interests,
                "pace": trip.pace
            }
        }

    @classmethod
    async def get_or_create_conversation(
        cls,
        db: AsyncSession,
        trip_id: uuid.UUID
    ) -> Conversation:
        stmt = select(Conversation).where(Conversation.trip_id == trip_id)
        res = await db.execute(stmt)
        conv = res.scalars().first()
        if not conv:
            conv = Conversation(trip_id=trip_id, title="Trip Assistant Conversation")
            db.add(conv)
            await db.flush()
        return conv

    @classmethod
    async def append_message(
        cls,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        sender: str,
        message: str,
        intent: Optional[str] = None,
        extracted_entities: Optional[Dict[str, Any]] = None,
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            sender=sender,
            message=message,
            intent=intent,
            extracted_entities=extracted_entities or {},
            state_snapshot=state_snapshot or {}
        )
        db.add(msg)
        await db.flush()
        return msg
