import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.core.logging import logger
from app.models.itinerary import Itinerary, ItineraryItem
from app.models.search import SearchResult
from app.models.trip import Trip
from app.providers.mock_activities import MockActivityProvider
from app.providers.mock_flights import MockFlightProvider
from app.providers.mock_hotels import MockHotelProvider
from app.providers.mock_transfers import MockTransferProvider
from app.services.audit_service import AuditService
from app.services.cost_service import CostService


class ReplanningService:
    def __init__(self):
        self.flight_provider = MockFlightProvider()
        self.hotel_provider = MockHotelProvider()
        self.activity_provider = MockActivityProvider()
        self.transfer_provider = MockTransferProvider()

    async def replan_itinerary(
        self,
        db: AsyncSession,
        trip: Trip,
        itinerary_id: uuid.UUID,
        target_budget: Optional[float] = None,
        change_flight: bool = False,
        change_hotel: bool = False,
        change_activities: bool = False,
        new_dates: Optional[tuple[date, date]] = None,
        removed_activity_ids: Optional[List[str]] = None,
        explanation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dependency-aware partial replanning preserving approved components."""
        stmt = select(Itinerary).where(Itinerary.id == itinerary_id, Itinerary.trip_id == trip.id)
        res = await db.execute(stmt)
        itinerary = res.scalars().first()
        if not itinerary:
            raise ResourceNotFoundException("Itinerary", itinerary_id)

        items_stmt = select(ItineraryItem).where(ItineraryItem.itinerary_id == itinerary.id).order_by(ItineraryItem.day_number)
        items_res = await db.execute(items_stmt)
        items = items_res.scalars().all()

        modified_components: List[str] = []
        destination = trip.destination or "Goa"

        # 1. Budget reduction re-evaluation
        if target_budget and (trip.budget_amount is None or target_budget < (trip.budget_amount or 100000)):
            trip.budget_amount = target_budget
            modified_components.append("budget_target")
            # Automatically find cheaper components
            if not change_hotel and not change_flight:
                change_hotel = True
                change_flight = True

        # 2. Flight change (keeping hotel & activities)
        if change_flight:
            available_flights = await self.flight_provider.search_flights(
                origin=trip.origin or "DEL",
                destination=destination,
                passengers=trip.number_of_travellers,
                cabin_class="economy"
            )
            if available_flights:
                # Sort by price ascending to fit budget
                available_flights.sort(key=lambda x: x.get("total_price", x.get("price", 0.0)))
                new_flight = available_flights[0]

                # Update flight in day 1 transport and search results
                if items:
                    day1 = items[0]
                    day1.transport = {
                        "category": "FLIGHT",
                        "airline": new_flight.get("airline"),
                        "flight_number": new_flight.get("flight_number"),
                        "departure_time": new_flight.get("departure_time"),
                        "total_price": new_flight.get("total_price", new_flight.get("price", 0.0))
                    }
                modified_components.append("flight")

        # 3. Hotel change (keeping flights & activities)
        if change_hotel:
            # Pick budget or balanced hotel according to new budget
            max_p = (target_budget * 0.35 / 4) if target_budget else 4000.0
            hotels = await self.hotel_provider.search_hotels(
                city=destination,
                max_price_per_night=max_p
            )
            if not hotels:
                hotels = await self.hotel_provider.search_hotels(city=destination)
            
            if hotels:
                hotels.sort(key=lambda x: x.get("total_price", x.get("price_per_night", 0.0)))
                new_hotel = hotels[0]
                for itm in items:
                    itm.hotel = {
                        "id": new_hotel.get("id"),
                        "name": new_hotel.get("name"),
                        "category": new_hotel.get("category"),
                        "price_per_night": new_hotel.get("price_per_night"),
                        "total_price": new_hotel.get("total_price")
                    }
                modified_components.append("hotel")

        # 4. Activity removal or re-selection
        if removed_activity_ids:
            for itm in items:
                if itm.activities:
                    itm.activities = [
                        a for a in itm.activities
                        if a.get("id") not in removed_activity_ids
                    ]
            modified_components.append("activities_removed")

        # 5. Date adjustment
        if new_dates:
            trip.start_date, trip.end_date = new_dates
            trip.duration_days = (new_dates[1] - new_dates[0]).days + 1
            modified_components.append("dates")

        # 6. Recalculate itinerary item costs and total
        total_itinerary_cost = 0.0
        for itm in items:
            day_cost = 0.0
            if itm.activities:
                for a in itm.activities:
                    day_cost += float(a.get("price", a.get("total_price", 0.0)))
            if itm.day_number == 1 and itm.hotel and "total_price" in itm.hotel:
                day_cost += float(itm.hotel["total_price"])
            if itm.day_number == 1 and itm.transport and "total_price" in itm.transport:
                day_cost += float(itm.transport["total_price"])
            
            itm.estimated_cost = round(day_cost, 2)
            total_itinerary_cost += day_cost

        itinerary.total_estimated_cost = round(total_itinerary_cost, 2)
        itinerary.title = f"{itinerary.tier} Itinerary (Updated / Partially Replanned)"
        itinerary.highlights.append(f"Replanned on {datetime.now(timezone.utc).strftime('%b %d')}: {', '.join(modified_components)}")

        await db.flush()

        # Recalculate full cost breakdown
        cost_breakdown = await CostService.calculate_trip_cost(db=db, trip_id=trip.id, itinerary_id=itinerary.id)

        await AuditService.log_action(
            db=db,
            action="PARTIAL_REPLANNING_COMPLETED",
            actor="SYSTEM",
            trip_id=trip.id,
            input_data={
                "itinerary_id": str(itinerary_id),
                "target_budget": target_budget,
                "modified_components": modified_components
            },
            result={"new_total": cost_breakdown.total, "currency": cost_breakdown.currency}
        )

        return {
            "success": True,
            "itinerary_id": str(itinerary.id),
            "modified_components": modified_components,
            "new_total": cost_breakdown.total,
            "currency": cost_breakdown.currency,
            "cost_breakdown": cost_breakdown.model_dump(),
            "explanation": explanation or f"Successfully preserved approved options while updating {', '.join(modified_components)}."
        }
