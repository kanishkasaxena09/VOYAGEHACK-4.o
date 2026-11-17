import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import TransferProvider


class MockTransferProvider(TransferProvider):
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or (settings.MOCK_DATA_DIR / "transfers.json")
        self._transfers: List[Dict[str, Any]] = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        if not self.data_file.exists():
            logger.warning(f"Mock transfer file {self.data_file} not found. Returning empty list.")
            return []
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read mock transfers: {e}")
            return []

    async def search_transfers(
        self,
        city: str,
        passengers: int = 2,
        vehicle_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        results = []
        city_clean = city.strip().upper() if city else ""

        for tr in self._transfers:
            t_city = tr.get("city", "").upper()
            if city_clean and not (city_clean in t_city or t_city in city_clean):
                continue

            if tr.get("capacity_passengers", 4) < passengers:
                continue

            if vehicle_type and vehicle_type.lower() not in tr.get("vehicle_type", "").lower():
                continue

            tr_copy = dict(tr)
            tr_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
            tr_copy["passengers"] = passengers
            tr_copy["total_price"] = tr.get("price", 0.0)
            results.append(tr_copy)

        if not results and self._transfers:
            for tr in self._transfers:
                tr_copy = dict(tr)
                tr_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
                tr_copy["passengers"] = passengers
                tr_copy["total_price"] = tr.get("price", 0.0)
                results.append(tr_copy)

        return results

    async def get_transfer_details(self, transfer_id: str) -> Optional[Dict[str, Any]]:
        for tr in self._transfers:
            if tr.get("id") == transfer_id:
                res = dict(tr)
                res["checked_at"] = datetime.now(timezone.utc).isoformat()
                return res
        return None
