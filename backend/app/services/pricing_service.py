from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from app.core.exceptions import StalePricingException, ValidationException
from app.providers.mock_flights import MockFlightProvider
from app.providers.mock_hotels import MockHotelProvider
from app.providers.mock_activities import MockActivityProvider
from app.providers.mock_transfers import MockTransferProvider
from app.schemas.pricing import PriceValidationResponse


class PricingService:
    MAX_PRICE_AGE_MINUTES: int = 30

    def __init__(self):
        self.flight_provider = MockFlightProvider()
        self.hotel_provider = MockHotelProvider()
        self.activity_provider = MockActivityProvider()
        self.transfer_provider = MockTransferProvider()

    def is_price_stale(self, checked_at: datetime) -> bool:
        """Determines if a price quote is stale based on elapsed time."""
        now = datetime.now(timezone.utc)
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=timezone.utc)
        return (now - checked_at) > timedelta(minutes=self.MAX_PRICE_AGE_MINUTES)

    async def validate_component_price(
        self,
        category: str,
        item_id: str,
        expected_price: float,
        currency: str = "INR"
    ) -> PriceValidationResponse:
        """Revalidates price and live availability with the provider."""
        cat = category.upper()
        provider_name = ""
        current_price = 0.0
        available = False
        now = datetime.now(timezone.utc)

        if cat == "FLIGHT":
            provider_name = "MockAirlines"
            item = await self.flight_provider.get_flight_details(item_id)
            if item:
                current_price = item.get("price", 0.0)
                available = item.get("available_seats", 0) > 0
        elif cat == "HOTEL":
            provider_name = "MockHotels"
            item = await self.hotel_provider.get_hotel_details(item_id)
            if item:
                current_price = item.get("total_price", item.get("price_per_night", 0.0) * 4)
                available = item.get("available_rooms", 0) > 0
        elif cat == "ACTIVITY":
            provider_name = "MockActivities"
            item = await self.activity_provider.get_activity_details(item_id)
            if item:
                current_price = item.get("price_per_person", 0.0) * 2
                available = item.get("available_slots", 0) > 0
        elif cat == "TRANSFER":
            provider_name = "MockTransfers"
            item = await self.transfer_provider.get_transfer_details(item_id)
            if item:
                current_price = item.get("price", 0.0)
                available = item.get("available", True)
        else:
            raise ValidationException(f"Unsupported component category: {category}")

        if not item:
            return PriceValidationResponse(
                item_id=item_id,
                category=cat,
                provider=provider_name or "Unknown",
                quoted_price=expected_price,
                current_price=0.0,
                currency=currency,
                is_valid=False,
                is_stale=True,
                price_changed=True,
                available=False,
                message=f"Item {item_id} is no longer found in provider inventory.",
                checked_at=now
            )

        price_changed = abs(current_price - expected_price) > 0.01
        is_valid = available and not price_changed

        msg = "Price and availability verified."
        if not available:
            msg = "Item is currently sold out."
        elif price_changed:
            msg = f"Price has updated from {expected_price} to {current_price} {currency}."

        return PriceValidationResponse(
            item_id=item_id,
            category=cat,
            provider=provider_name,
            quoted_price=expected_price,
            current_price=current_price,
            currency=currency,
            is_valid=is_valid,
            is_stale=False,
            price_changed=price_changed,
            available=available,
            message=msg,
            checked_at=now
        )
