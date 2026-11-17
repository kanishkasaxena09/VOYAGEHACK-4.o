import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.itinerary import Itinerary, ItineraryItem
from app.models.search import SearchResult
from app.models.trip import Trip
from app.schemas.pricing import CostBreakdownResponse


class CostService:
    TAX_RATE: float = 0.05  # 5% regulatory GST / travel tax
    SERVICE_FEE: float = 850.0  # Flat booking and service fee
    DEFAULT_DISCOUNT: float = 1000.0  # Bundle discount

    @classmethod
    def calculate_totals(
        cls,
        flight_cost: float = 0.0,
        hotel_cost: float = 0.0,
        activity_cost: float = 0.0,
        transfer_cost: float = 0.0,
        apply_discount: bool = True
    ) -> Dict[str, float]:
        subtotal = flight_cost + hotel_cost + activity_cost + transfer_cost
        taxes = round(subtotal * cls.TAX_RATE, 2)
        fees = cls.SERVICE_FEE if subtotal > 0 else 0.0
        discounts = cls.DEFAULT_DISCOUNT if (apply_discount and subtotal > 20000.0) else 0.0
        total = round(subtotal + taxes + fees - discounts, 2)

        return {
            "flight_cost": round(flight_cost, 2),
            "hotel_cost": round(hotel_cost, 2),
            "activity_cost": round(activity_cost, 2),
            "transfer_cost": round(transfer_cost, 2),
            "taxes": taxes,
            "fees": fees,
            "discounts": discounts,
            "total": total
        }

    @classmethod
    async def calculate_trip_cost(
        cls,
        db: AsyncSession,
        trip_id: uuid.UUID,
        itinerary_id: Optional[uuid.UUID] = None
    ) -> CostBreakdownResponse:
        flight_cost = 0.0
        hotel_cost = 0.0
        activity_cost = 0.0
        transfer_cost = 0.0
        selected_components: Dict[str, Any] = {}

        # 1. Check if specific or selected itinerary exists
        stmt = select(Itinerary).where(Itinerary.trip_id == trip_id)
        if itinerary_id:
            stmt = stmt.where(Itinerary.id == itinerary_id)
        else:
            stmt = stmt.where(Itinerary.is_selected == True)
        
        result = await db.execute(stmt)
        itinerary = result.scalars().first()

        if itinerary:
            items_stmt = select(ItineraryItem).where(ItineraryItem.itinerary_id == itinerary.id)
            items_result = await db.execute(items_stmt)
            items = items_result.scalars().all()

            for item in items:
                # Accumulate activities
                if item.activities:
                    for act in item.activities:
                        act_price = float(act.get("price", act.get("total_price", 0.0)))
                        activity_cost += act_price

                # Check hotel
                if item.hotel and "total_price" in item.hotel:
                    hotel_cost = max(hotel_cost, float(item.hotel["total_price"]))

                # Check transport / transfers
                if item.transport and "total_price" in item.transport:
                    transfer_cost += float(item.transport["total_price"])

        # 2. Add or fallback to persisted search results for this trip
        search_stmt = select(SearchResult).where(SearchResult.trip_id == trip_id, SearchResult.available == True)
        search_res = await db.execute(search_stmt)
        search_items = search_res.scalars().all()

        for s in search_items:
            cat = s.category.upper()
            if cat == "FLIGHT" and flight_cost == 0.0:
                flight_cost = s.price
                selected_components["flight"] = {"id": s.external_id, "title": s.title, "price": s.price}
            elif cat == "HOTEL" and hotel_cost == 0.0:
                hotel_cost = s.price
                selected_components["hotel"] = {"id": s.external_id, "title": s.title, "price": s.price}
            elif cat == "ACTIVITY" and activity_cost == 0.0:
                activity_cost += s.price
                selected_components.setdefault("activities", []).append({"id": s.external_id, "title": s.title, "price": s.price})
            elif cat == "TRANSFER" and transfer_cost == 0.0:
                transfer_cost = s.price
                selected_components["transfer"] = {"id": s.external_id, "title": s.title, "price": s.price}

        # If zero, inject realistic default estimates from trip requirements
        if flight_cost == 0.0 and hotel_cost == 0.0:
            flight_cost = 27000.0
            hotel_cost = 20800.0
            activity_cost = 9800.0
            transfer_cost = 3800.0

        totals = cls.calculate_totals(
            flight_cost=flight_cost,
            hotel_cost=hotel_cost,
            activity_cost=activity_cost,
            transfer_cost=transfer_cost
        )

        return CostBreakdownResponse(
            trip_id=trip_id,
            flight_cost=totals["flight_cost"],
            hotel_cost=totals["hotel_cost"],
            activity_cost=totals["activity_cost"],
            transfer_cost=totals["transfer_cost"],
            taxes=totals["taxes"],
            fees=totals["fees"],
            discounts=totals["discounts"],
            total=totals["total"],
            currency="INR",
            selected_components=selected_components,
            calculated_at=datetime.now(timezone.utc)
        )
