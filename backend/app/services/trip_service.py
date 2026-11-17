import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import ForbiddenException, ResourceNotFoundException
from app.models.preference import ConstraintSeverity, TripConstraint, TripPreference
from app.models.traveller import Traveller
from app.models.trip import Trip, TripStatus
from app.schemas.trip import PreferenceCreate, TripCreate, TripUpdate
from app.services.audit_service import AuditService


class TripService:
    @classmethod
    async def get_user_trip(
        cls,
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Trip:
        stmt = (
            select(Trip)
            .where(Trip.id == trip_id)
            .options(
                selectinload(Trip.preferences),
                selectinload(Trip.constraints),
                selectinload(Trip.travellers),
                selectinload(Trip.itineraries),
                selectinload(Trip.bookings)
            )
        )
        res = await db.execute(stmt)
        trip = res.scalars().first()
        if not trip:
            raise ResourceNotFoundException("Trip", trip_id)
        if trip.user_id != user_id:
            raise ForbiddenException("You do not have access to this trip.")
        return trip

    @classmethod
    async def list_user_trips(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[Trip]:
        stmt = (
            select(Trip)
            .where(Trip.user_id == user_id)
            .options(
                selectinload(Trip.preferences),
                selectinload(Trip.constraints),
                selectinload(Trip.travellers)
            )
            .order_by(Trip.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def create_trip(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        trip_in: TripCreate
    ) -> Trip:
        trip = Trip(
            user_id=user_id,
            title=trip_in.title or "My Upcoming Trip",
            status=TripStatus.INSPIRATION,
            origin=trip_in.origin,
            destination=trip_in.destination,
            start_date=trip_in.start_date,
            end_date=trip_in.end_date,
            duration_days=trip_in.duration_days,
            number_of_travellers=trip_in.number_of_travellers,
            budget_amount=trip_in.budget_amount,
            budget_currency=trip_in.budget_currency,
            purpose=trip_in.purpose,
            interests=trip_in.interests or [],
            pace=trip_in.pace or "relaxed"
        )
        db.add(trip)
        await db.flush()

        # Preferences
        pref_in = trip_in.preferences or PreferenceCreate()
        pref = TripPreference(
            trip_id=trip.id,
            hotel_category=pref_in.hotel_category,
            preferred_airline=pref_in.preferred_airline,
            cabin_class=pref_in.cabin_class,
            nonstop_required=pref_in.nonstop_required,
            max_flight_duration_minutes=pref_in.max_flight_duration_minutes,
            food_preferences=pref_in.food_preferences or [],
            activity_preferences=pref_in.activity_preferences or [],
            pace=pref_in.pace or "relaxed",
            accessibility_requirements=pref_in.accessibility_requirements or [],
            things_to_avoid=pref_in.things_to_avoid or [],
            extra_preferences=pref_in.extra_preferences or {}
        )
        db.add(pref)

        # Constraints
        if trip_in.constraints:
            for c_in in trip_in.constraints:
                c = TripConstraint(
                    trip_id=trip.id,
                    constraint_type=c_in.constraint_type,
                    value=c_in.value,
                    severity=c_in.severity,
                    description=c_in.description
                )
                db.add(c)

        if trip.budget_amount:
            b_c = TripConstraint(
                trip_id=trip.id,
                constraint_type="MAX_BUDGET",
                value=str(trip.budget_amount),
                severity=ConstraintSeverity.HARD,
                description=f"Maximum budget of {trip.budget_currency} {trip.budget_amount}"
            )
            db.add(b_c)

        await db.flush()

        await AuditService.log_action(
            db=db,
            action="TRIP_CREATED",
            actor="USER",
            trip_id=trip.id,
            user_id=user_id,
            result={"trip_id": str(trip.id), "status": trip.status}
        )

        return trip

    @classmethod
    async def update_trip(
        cls,
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID,
        trip_update: TripUpdate
    ) -> Trip:
        trip = await cls.get_user_trip(db, trip_id, user_id)
        update_data = trip_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(trip, field, value)

        await db.flush()

        await AuditService.log_action(
            db=db,
            action="TRIP_UPDATED",
            actor="USER",
            trip_id=trip.id,
            user_id=user_id,
            input_data=update_data
        )

        return trip

    @classmethod
    async def delete_trip(
        cls,
        db: AsyncSession,
        trip_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> None:
        trip = await cls.get_user_trip(db, trip_id, user_id)
        await db.delete(trip)
        await db.flush()

        await AuditService.log_action(
            db=db,
            action="TRIP_DELETED",
            actor="USER",
            trip_id=trip_id,
            user_id=user_id
        )
