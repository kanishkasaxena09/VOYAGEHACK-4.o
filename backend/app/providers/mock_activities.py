import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.providers.base import ActivityProvider


class MockActivityProvider(ActivityProvider):
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or (settings.MOCK_DATA_DIR / "activities.json")
        self._activities: List[Dict[str, Any]] = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        if not self.data_file.exists():
            logger.warning(f"Mock activity file {self.data_file} not found. Returning empty list.")
            return []
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read mock activities: {e}")
            return []

    async def search_activities(
        self,
        city: str,
        category: Optional[str] = None,
        activity_date: Optional[date] = None,
        participants: int = 2
    ) -> List[Dict[str, Any]]:
        results = []
        city_clean = city.strip().upper() if city else ""

        for act in self._activities:
            a_city = act.get("city", "").upper()
            if city_clean and not (city_clean in a_city or a_city in city_clean):
                continue

            if category and category.lower() not in act.get("category", "").lower():
                continue

            if act.get("available_slots", 0) < participants:
                continue

            act_copy = dict(act)
            act_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
            act_copy["participants"] = participants
            act_copy["total_price"] = act.get("price_per_person", 0.0) * participants
            act_copy["available"] = True
            results.append(act_copy)

        if not results and self._activities:
            for act in self._activities:
                act_copy = dict(act)
                act_copy["checked_at"] = datetime.now(timezone.utc).isoformat()
                act_copy["participants"] = participants
                act_copy["total_price"] = act.get("price_per_person", 0.0) * participants
                act_copy["available"] = True
                results.append(act_copy)

        return results

    async def get_activity_details(self, activity_id: str) -> Optional[Dict[str, Any]]:
        for act in self._activities:
            if act.get("id") == activity_id:
                res = dict(act)
                res["checked_at"] = datetime.now(timezone.utc).isoformat()
                return res
        return None
