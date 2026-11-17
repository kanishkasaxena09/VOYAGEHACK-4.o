import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_booking_cancellation_and_modification(async_client: AsyncClient, auth_headers: dict):
    # 1. Create Trip
    trip_res = await async_client.post(
        "/api/trips",
        json={"title": "Booking Demo Trip", "destination": "Goa", "number_of_travellers": 2, "budget_amount": 80000.0},
        headers=auth_headers
    )
    trip_id = trip_res.json()["data"]["id"]

    # 2. Prepare Booking (creates PendingAction)
    prep_res = await async_client.post(f"/api/trips/{trip_id}/booking/prepare", headers=auth_headers)
    assert prep_res.status_code == 200
    pending_data = prep_res.json()["data"]
    pending_id = pending_data["id"]
    idempotency_key = pending_data["idempotency_key"]
    assert pending_data["status"] == "AWAITING_CONFIRMATION"

    # 3. Confirm Booking with Idempotency Key
    confirm_res = await async_client.post(
        f"/api/trips/{trip_id}/booking/confirm",
        json={"pending_action_id": pending_id, "idempotency_key": idempotency_key},
        headers=auth_headers
    )
    assert confirm_res.status_code == 200
    booking_data = confirm_res.json()["data"]
    booking_id = booking_data["id"]
    assert booking_data["status"] == "CONFIRMED"
    assert booking_data["booking_reference"].startswith("BKG-")
    assert booking_data["voucher_data"] is not None

    # Idempotent re-submission should return same confirmed booking
    dup_res = await async_client.post(
        f"/api/trips/{trip_id}/booking/confirm",
        json={"pending_action_id": pending_id, "idempotency_key": idempotency_key},
        headers=auth_headers
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["data"]["id"] == booking_id

    # 4. Check Vouchers
    voucher_res = await async_client.get(f"/api/trips/{trip_id}/vouchers", headers=auth_headers)
    assert voucher_res.status_code == 200
    vouchers = voucher_res.json()["data"]
    assert len(vouchers) >= 1
    assert vouchers[0]["booking_reference"] == booking_data["booking_reference"]

    # 5. Prepare Cancellation
    prep_cancel = await async_client.post(
        f"/api/bookings/{booking_id}/cancel/prepare",
        json={"reason": "Schedule change"},
        headers=auth_headers
    )
    assert prep_cancel.status_code == 200
    cancel_action = prep_cancel.json()["data"]
    cancel_action_id = cancel_action["id"]
    assert cancel_action["details"]["expected_refund"] > 0

    # 6. Confirm Cancellation
    confirm_cancel = await async_client.post(
        f"/api/bookings/{booking_id}/cancel/confirm",
        json={"pending_action_id": cancel_action_id, "idempotency_key": f"cnx-key-{booking_id}"},
        headers=auth_headers
    )
    assert confirm_cancel.status_code == 200
    assert confirm_cancel.json()["data"]["status"] == "CANCELLED"
