import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.models.booking import Booking, BookingItem
from app.models.disruption import Disruption, DisruptionStatus
from app.models.pending_action import ActionStatus, ActionType, PendingAction
from app.models.trip import Trip
from app.schemas.disruption import DisruptionResponse
from app.services.audit_service import AuditService
from app.services.confirmation_service import ConfirmationService


class DisruptionAgent:
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or (settings.MOCK_DATA_DIR / "disruptions.json")
        self._mock_disruptions = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        if not self.data_file.exists():
            return []
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    async def check_and_detect_disruptions(
        self,
        db: AsyncSession,
        trip_id: uuid.UUID
    ) -> List[DisruptionResponse]:
        """Detect disruptions for a trip's active bookings."""
        # Find existing recorded disruptions
        stmt = select(Disruption).where(Disruption.trip_id == trip_id)
        res = await db.execute(stmt)
        existing = list(res.scalars().all())

        if not existing and self._mock_disruptions:
            # Seed mock disruption for demo
            mock_d = self._mock_disruptions[0]  # e.g., Flight cancelled
            disrupt = Disruption(
                trip_id=trip_id,
                disruption_type=mock_d.get("type", "FLIGHT_CANCELLED"),
                target_type=mock_d.get("target_type", "FLIGHT"),
                reference_id=mock_d.get("reference_id", "FL-GOA-101"),
                severity=mock_d.get("severity", "CRITICAL"),
                reason=mock_d.get("reason", "Operational technical check"),
                status=DisruptionStatus.DETECTED,
                impact_summary=mock_d.get("impact_summary"),
                original_data=mock_d,
                alternative_options=mock_d.get("alternatives", []),
                selected_option=None
            )
            db.add(disrupt)
            await db.flush()

            await AuditService.log_action(
                db=db,
                action="DISRUPTION_DETECTED",
                actor="SYSTEM",
                trip_id=trip_id,
                input_data={"disruption_type": disrupt.disruption_type, "target_type": disrupt.target_type},
                result={"disruption_id": str(disrupt.id), "severity": disrupt.severity}
            )

            existing.append(disrupt)

        return [DisruptionResponse.model_validate(d) for d in existing]

    async def get_disruption_options(
        self,
        db: AsyncSession,
        trip_id: uuid.UUID,
        disruption_id: uuid.UUID
    ) -> Dict[str, Any]:
        stmt = select(Disruption).where(Disruption.id == disruption_id, Disruption.trip_id == trip_id)
        res = await db.execute(stmt)
        disrupt = res.scalars().first()
        if not disrupt:
            raise ResourceNotFoundException("Disruption", disruption_id)

        disrupt.status = DisruptionStatus.OPTIONS_PRESENTED
        await db.flush()

        return {
            "disruption_id": str(disrupt.id),
            "type": disrupt.disruption_type,
            "reason": disrupt.reason,
            "impact_summary": disrupt.impact_summary,
            "alternatives": disrupt.alternative_options,
            "action_required": "Please choose an alternative option to confirm rebooking or refund."
        }

    async def confirm_disruption_resolution(
        self,
        db: AsyncSession,
        trip: Trip,
        disruption_id: uuid.UUID,
        alternative_id: str,
        idempotency_key: str
    ) -> Dict[str, Any]:
        """Human confirms selection for resolution; executes rebooking or refund."""
        stmt = select(Disruption).where(Disruption.id == disruption_id, Disruption.trip_id == trip.id)
        res = await db.execute(stmt)
        disrupt = res.scalars().first()
        if not disrupt:
            raise ResourceNotFoundException("Disruption", disruption_id)

        # Match alternative
        selected = next((alt for alt in disrupt.alternative_options if alt.get("alternative_id") == alternative_id), None)
        if not selected:
            raise ValidationException(f"Alternative option '{alternative_id}' not found.")

        disrupt.status = DisruptionStatus.RESOLVED
        disrupt.selected_option = selected

        # Update affected booking if present
        b_stmt = select(Booking).where(Booking.trip_id == trip.id).options(selectinload(Booking.items))
        b_res = await db.execute(b_stmt)
        bookings = b_res.scalars().all()

        for b in bookings:
            for itm in b.items:
                if itm.category == disrupt.target_type:
                    itm.status = "REBOOKED" if "refund" not in alternative_id.lower() else "REFUNDED"
                    itm.title = f"{itm.title} (Resolved: {selected.get('description', '')})"

        await AuditService.log_action(
            db=db,
            action="DISRUPTION_RESOLVED",
            actor="USER",
            trip_id=trip.id,
            user_id=trip.user_id,
            input_data={"disruption_id": str(disruption_id), "alternative_id": alternative_id, "idempotency_key": idempotency_key},
            result={"status": "RESOLVED", "selected_option": selected}
        )

        await db.flush()

        return {
            "success": True,
            "disruption_id": str(disrupt.id),
            "status": "RESOLVED",
            "resolution_summary": f"Disruption successfully resolved with: {selected.get('description')}",
            "applied_option": selected
        }
