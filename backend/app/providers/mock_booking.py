import random
import string
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.exceptions import ValidationException
from app.providers.base import BookingProvider


class MockBookingProvider(BookingProvider):
    def _generate_booking_reference(self, prefix: str = "TRV") -> str:
        random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=7))
        return f"{prefix}-{random_str}"

    async def create_booking(
        self,
        trip_id: str,
        user_id: str,
        components: List[Dict[str, Any]],
        idempotency_key: str
    ) -> Dict[str, Any]:
        if not components:
            raise ValidationException("Cannot execute booking with empty components.")

        booking_ref = self._generate_booking_reference("BKG")
        items = []
        total_amount = 0.0
        currency = "INR"

        for item in components:
            cat = item.get("category", "FLIGHT").upper()
            prefix_map = {
                "FLIGHT": "TKT",
                "HOTEL": "HTL",
                "ACTIVITY": "ACT",
                "TRANSFER": "TRF"
            }
            item_pnr = self._generate_booking_reference(prefix_map.get(cat, "RES"))
            item_price = float(item.get("price", 0.0))
            total_amount += item_price
            currency = item.get("currency", currency)

            items.append({
                "id": str(uuid.uuid4()),
                "category": cat,
                "provider": item.get("provider", "MockTravelProvider"),
                "provider_booking_id": item_pnr,
                "title": item.get("title", f"Booked {cat}"),
                "price": item_price,
                "currency": currency,
                "status": "CONFIRMED",
                "cancellation_policy": item.get("cancellation_policy", "Standard cancellation terms apply."),
                "details": item.get("details", {})
            })

        voucher_data = {
            "voucher_code": f"VOUCHER-{booking_ref}",
            "issued_at": datetime.now(timezone.utc).isoformat(),
            "valid_until": "2026-12-31T23:59:59Z",
            "qr_data": f"https://api.travelagent.internal/vouchers/verify/{booking_ref}",
            "contact_support": "support@travelagent.internal",
            "items_count": len(items)
        }

        return {
            "booking_reference": booking_ref,
            "status": "CONFIRMED",
            "total_amount": round(total_amount, 2),
            "currency": currency,
            "idempotency_key": idempotency_key,
            "items": items,
            "voucher_data": voucher_data,
            "cancellation_policy": "Standard provider cancellation: Refundable up to 48 hours prior with nominal cancellation fee.",
            "penalty_fee": 2500.0,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }

    async def cancel_booking(
        self,
        booking_reference: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        penalty = 2500.0
        return {
            "booking_reference": booking_reference,
            "status": "CANCELLED",
            "penalty_fee": penalty,
            "cancellation_policy": "Provider penalty applied. Remaining balance queued for refund.",
            "cancellation_code": f"CNX-{booking_reference}",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason or "User requested cancellation"
        }

    async def modify_booking(
        self,
        booking_reference: str,
        modification_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        modification_fee = 1000.0
        return {
            "booking_reference": booking_reference,
            "status": "MODIFIED",
            "modification_fee": modification_fee,
            "details": modification_details,
            "modified_at": datetime.now(timezone.utc).isoformat()
        }
