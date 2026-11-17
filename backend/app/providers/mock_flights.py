import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import FlightProvider


class MockFlightProvider(FlightProvider):
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or (settings.MOCK_DATA_DIR / "flights.json")
        self._flights: List[Dict[str, Any]] = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        if not self.data_file.exists():
            logger.warning(f"Mock flight file {self.data_file} not found. Returning empty list.")
            return []
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read mock flights: {e}")
            return []

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[date] = None,
        return_date: Optional[date] = None,
        passengers: int = 1,
        cabin_class: Optional[str] = "economy",
        nonstop_only: bool = False
    ) -> List[Dict[str, Any]]:
        results = []
        origin_clean = origin.strip().upper() if origin else ""
        dest_clean = destination.strip().upper() if destination else ""

        for flight in self._flights:
            f_orig = flight.get("origin", "").upper()
            f_orig_city = flight.get("origin_city", "").upper()
            f_dest = flight.get("destination", "").upper()
            f_dest_city = flight.get("destination_city", "").upper()

            # Origin match
            if origin_clean and not (origin_clean in f_orig or origin_clean in f_orig_city):
                continue

            # Destination match
            if dest_clean and not (dest_clean in f_dest or dest_clean in f_dest_city):
                continue

            # Nonstop filter
            if nonstop_only and flight.get("stops", 0) > 0:
                continue

            # Cabin class filter
            if cabin_class and flight.get("cabin_class", "economy").lower() != cabin_class.lower():
                continue

            # Availability check
            if flight.get("available_seats", 0) < passengers:
                continue

            # Dynamic price scaling for passenger count
            flight_copy = dict(flight)
            flight_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
            flight_copy["passenger_count"] = passengers
            flight_copy["total_price"] = flight.get("price", 0.0) * passengers
            results.append(flight_copy)

        # Fallback if no strict match but destination provided, return closest mock match
        if not results and dest_clean:
            for flight in self._flights:
                f_dest = flight.get("destination", "").upper()
                f_dest_city = flight.get("destination_city", "").upper()
                if dest_clean in f_dest or dest_clean in f_dest_city or f_dest_city in dest_clean:
                    flight_copy = dict(flight)
                    flight_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
                    flight_copy["passenger_count"] = passengers
                    flight_copy["total_price"] = flight.get("price", 0.0) * passengers
                    results.append(flight_copy)

        return results

    async def get_flight_details(self, flight_id: str) -> Optional[Dict[str, Any]]:
        for flight in self._flights:
            if flight.get("id") == flight_id:
                res = dict(flight)
                res["checked_at"] = datetime.now(timezone.utc).isoformat()
                return res
        return None
