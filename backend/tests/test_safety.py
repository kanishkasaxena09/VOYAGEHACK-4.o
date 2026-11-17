import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.pending_action import ActionStatus, PendingAction
from tests.conftest import test_session_factory


@pytest.mark.asyncio
async def test_booking_cannot_happen_without_confirmation(async_client: AsyncClient, auth_headers: dict):
    # Attempting to call confirm booking with fake/unprepared action ID must fail
    fake_id = str(uuid.uuid4())
    res = await async_client.post(
        f"/api/trips/{uuid.uuid4()}/booking/confirm",
        json={"pending_action_id": fake_id, "idempotency_key": "some-key"},
        headers=auth_headers
    )
    assert res.status_code == 404
    assert res.json()["success"] is False


@pytest.mark.asyncio
async def test_user_a_cannot_access_user_b_trip(
    async_client: AsyncClient,
    auth_headers: dict,
    user_b_headers: dict
):
    # User A creates a trip
    res_a = await async_client.post(
        "/api/trips",
        json={"title": "User A Private Trip", "destination": "Goa"},
        headers=auth_headers
    )
    assert res_a.status_code == 201
    trip_id = res_a.json()["data"]["id"]

    # User B tries to access User A's trip -> must return 403 Forbidden
    res_b = await async_client.get(f"/api/trips/{trip_id}", headers=user_b_headers)
    assert res_b.status_code == 403
    assert res_b.json()["error"]["code"] == "FORBIDDEN"

    # User B tries to chat on User A's trip -> must return 403 Forbidden
    chat_b = await async_client.post(
        f"/api/trips/{trip_id}/chat",
        json={"message": "Hack attempt"},
        headers=user_b_headers
    )
    assert chat_b.status_code == 403


@pytest.mark.asyncio
async def test_expired_confirmation_cannot_execute(async_client: AsyncClient, auth_headers: dict):
    # 1. Create trip & prepare booking
    trip_res = await async_client.post(
        "/api/trips",
        json={"title": "Expiry Test Trip", "destination": "Goa"},
        headers=auth_headers
    )
    trip_id = trip_res.json()["data"]["id"]

    prep_res = await async_client.post(f"/api/trips/{trip_id}/booking/prepare", headers=auth_headers)
    pending_id = prep_res.json()["data"]["id"]
    idempotency_key = prep_res.json()["data"]["idempotency_key"]

    # 2. Artificially expire the pending action in DB
    async with test_session_factory() as db:
        stmt = select(PendingAction).where(PendingAction.id == uuid.UUID(pending_id))
        res = await db.execute(stmt)
        action = res.scalars().first()
        action.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        await db.commit()

    # 3. Confirming an expired pending action must fail with 410 Gone / CONFIRMATION_EXPIRED
    confirm_res = await async_client.post(
        f"/api/trips/{trip_id}/booking/confirm",
        json={"pending_action_id": pending_id, "idempotency_key": idempotency_key},
        headers=auth_headers
    )
    assert confirm_res.status_code == 410
    assert confirm_res.json()["error"]["code"] == "CONFIRMATION_EXPIRED"
