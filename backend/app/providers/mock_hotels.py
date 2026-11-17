import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import HotelProvider


class MockHotelProvider(HotelProvider):
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or (settings.MOCK_DATA_DIR / "hotels.json")
        self._hotels: List[Dict[str, Any]] = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        if not self.data_file.exists():
            logger.warning(f"Mock hotel file {self.data_file} not found. Returning empty list.")
            return []
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read mock hotels: {e}")
            return []

    async def search_hotels(
        self,
        city: str,
        check_in: Optional[date] = None,
        check_out: Optional[date] = None,
        guests: int = 2,
        category: Optional[str] = None,
        max_price_per_night: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        results = []
        city_clean = city.strip().upper() if city else ""

        # Calculate number of nights
        nights = 4
        if check_in and check_out:
            calculated_nights = (check_out - check_in).days
            if calculated_nights > 0:
                nights = calculated_nights

        for hotel in self._hotels:
            h_city = hotel.get("city", "").upper()
            h_loc = hotel.get("location", "").upper()

            if city_clean and not (city_clean in h_city or city_clean in h_loc or h_city in city_clean):
                continue

            if category and category.lower() not in hotel.get("category", "").lower():
                continue

            price_per_night = hotel.get("price_per_night", 0.0)
            if max_price_per_night and price_per_night > max_price_per_night:
                continue

            hotel_copy = dict(hotel)
            hotel_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
            hotel_copy["nights"] = nights
            hotel_copy["total_price"] = price_per_night * nights
            hotel_copy["available"] = hotel.get("available_rooms", 0) > 0
            results.append(hotel_copy)

        # Fallback if no strict city match, return available hotels
        if not results and self._hotels:
            for hotel in self._hotels:
                hotel_copy = dict(hotel)
                hotel_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
                hotel_copy["nights"] = nights
                hotel_copy["total_price"] = hotel.get("price_per_night", 0.0) * nights
                hotel_copy["available"] = hotel.get("available_rooms", 0) > 0
                results.append(hotel_copy)

        return results

    async def get_hotel_details(self, hotel_id: str) -> Optional[Dict[str, Any]]:
        for hotel in self._hotels:
            if hotel.get("id") == hotel_id:
                res = dict(hotel)
                res["checked_at"] = datetime.now(timezone.utc).isoformat()
                return res
        return None
