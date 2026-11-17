import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.search import SearchResult
from app.models.trip import Trip
from app.providers.mock_activities import MockActivityProvider
from app.providers.mock_flights import MockFlightProvider
from app.providers.mock_hotels import MockHotelProvider
from app.providers.mock_transfers import MockTransferProvider
from app.schemas.search import (
    SearchActivityRequest,
    SearchAllResponse,
    SearchFlightRequest,
    SearchHotelRequest,
    SearchResultResponse,
    SearchTransferRequest,
)
from app.services.audit_service import AuditService


class SearchAgent:
    def __init__(self):
        self.flight_provider = MockFlightProvider()
        self.hotel_provider = MockHotelProvider()
        self.activity_provider = MockActivityProvider()
        self.transfer_provider = MockTransferProvider()

    async def search_flights(
        self,
        db: AsyncSession,
        trip: Trip,
        req: Optional[SearchFlightRequest] = None
    ) -> List[SearchResultResponse]:
        origin = req.origin if req and req.origin else (trip.origin or "DEL")
        destination = req.destination if req and req.destination else (trip.destination or "Goa")
        passengers = req.passengers if req and req.passengers else trip.number_of_travellers

        flights_data = await self.flight_provider.search_flights(
            origin=origin,
            destination=destination,
            passengers=passengers,
            cabin_class=req.cabin_class if req else "economy",
            nonstop_only=req.nonstop_only if req else False
        )

        added_records = []
        for f in flights_data:
            sr = SearchResult(
                trip_id=trip.id,
                category="FLIGHT",
                provider=f.get("provider", "MockAirlines"),
                external_id=f.get("id"),
                title=f"{f.get('airline')} {f.get('flight_number')} ({f.get('origin')} → {f.get('destination')})",
                price=f.get("total_price", f.get("price")),
                currency=f.get("currency", "INR"),
                available=f.get("available_seats", 0) > 0,
                cancellation_policy=f.get("cancellation_policy"),
                penalty_fee=f.get("penalty_fee", 0.0),
                details=f,
                checked_at=datetime.now(timezone.utc),
                is_stale=False
            )
            db.add(sr)
            added_records.append(sr)

        await db.flush()
        return [SearchResultResponse.model_validate(sr) for sr in added_records]

    async def search_hotels(
        self,
        db: AsyncSession,
        trip: Trip,
        req: Optional[SearchHotelRequest] = None
    ) -> List[SearchResultResponse]:
        city = req.city if req and req.city else (trip.destination or "Goa")
        guests = req.guests if req and req.guests else trip.number_of_travellers
        hotels_data = await self.hotel_provider.search_hotels(
            city=city,
            guests=guests,
            category=req.category if req else None,
            max_price_per_night=req.max_price_per_night if req else None
        )

        added_records = []
        for h in hotels_data:
            sr = SearchResult(
                trip_id=trip.id,
                category="HOTEL",
                provider=h.get("provider", "MockHotels"),
                external_id=h.get("id"),
                title=f"{h.get('name')} ({h.get('category')})",
                price=h.get("total_price", h.get("price_per_night", 0.0) * 4),
                currency=h.get("currency", "INR"),
                available=h.get("available", True),
                cancellation_policy=h.get("cancellation_policy"),
                penalty_fee=h.get("penalty_fee", 0.0),
                details=h,
                checked_at=datetime.now(timezone.utc),
                is_stale=False
            )
            db.add(sr)
            added_records.append(sr)

        await db.flush()
        return [SearchResultResponse.model_validate(sr) for sr in added_records]

    async def search_activities(
        self,
        db: AsyncSession,
        trip: Trip,
        req: Optional[SearchActivityRequest] = None
    ) -> List[SearchResultResponse]:
        city = req.city if req and req.city else (trip.destination or "Goa")
        participants = req.participants if req and req.participants else trip.number_of_travellers
        acts_data = await self.activity_provider.search_activities(
            city=city,
            participants=participants,
            category=req.category if req else None
        )

        added_records = []
        for a in acts_data:
            sr = SearchResult(
                trip_id=trip.id,
                category="ACTIVITY",
                provider=a.get("provider", "MockActivities"),
                external_id=a.get("id"),
                title=a.get("title"),
                price=a.get("total_price", a.get("price_per_person", 0.0) * participants),
                currency=a.get("currency", "INR"),
                available=a.get("available", True),
                cancellation_policy=a.get("cancellation_policy"),
                penalty_fee=a.get("penalty_fee", 0.0),
                details=a,
                checked_at=datetime.now(timezone.utc),
                is_stale=False
            )
            db.add(sr)
            added_records.append(sr)

        await db.flush()
        return [SearchResultResponse.model_validate(sr) for sr in added_records]

    async def search_transfers(
        self,
        db: AsyncSession,
        trip: Trip,
        req: Optional[SearchTransferRequest] = None
    ) -> List[SearchResultResponse]:
        city = req.city if req and req.city else (trip.destination or "Goa")
        passengers = req.passengers if req and req.passengers else trip.number_of_travellers
        tr_data = await self.transfer_provider.search_transfers(
            city=city,
            passengers=passengers,
            vehicle_type=req.vehicle_type if req else None
        )

        added_records = []
        for t in tr_data:
            sr = SearchResult(
                trip_id=trip.id,
                category="TRANSFER",
                provider=t.get("provider", "MockTransfers"),
                external_id=t.get("id"),
                title=f"{t.get('category')} - {t.get('vehicle_type')}",
                price=t.get("total_price", t.get("price")),
                currency=t.get("currency", "INR"),
                available=t.get("available", True),
                cancellation_policy=t.get("cancellation_policy"),
                penalty_fee=t.get("penalty_fee", 0.0),
                details=t,
                checked_at=datetime.now(timezone.utc),
                is_stale=False
            )
            db.add(sr)
            added_records.append(sr)

        await db.flush()
        return [SearchResultResponse.model_validate(sr) for sr in added_records]

    async def search_all(
        self,
        db: AsyncSession,
        trip: Trip
    ) -> SearchAllResponse:
        f_list = await self.search_flights(db, trip)
        h_list = await self.search_hotels(db, trip)
        a_list = await self.search_activities(db, trip)
        t_list = await self.search_transfers(db, trip)

        await AuditService.log_action(
            db=db,
            action="SEARCH_PERFORMED",
            actor="SYSTEM",
            trip_id=trip.id,
            result={
                "flights_count": len(f_list),
                "hotels_count": len(h_list),
                "activities_count": len(a_list),
                "transfers_count": len(t_list)
            }
        )

        return SearchAllResponse(
            trip_id=trip.id,
            flights=f_list,
            hotels=h_list,
            activities=a_list,
            transfers=t_list
        )
