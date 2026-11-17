import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trip_crud_lifecycle(async_client: AsyncClient, auth_headers: dict):
    # Create trip
    trip_payload = {
        "title": "Relaxed Goa Beach Trip",
        "destination": "Goa",
        "origin": "DEL",
        "start_date": "2026-12-10",
        "end_date": "2026-12-14",
        "number_of_travellers": 2,
        "budget_amount": 80000.0,
        "budget_currency": "INR",
        "interests": ["beaches", "food", "relaxed"],
        "pace": "relaxed"
    }

    create_res = await async_client.post("/api/trips", json=trip_payload, headers=auth_headers)
    assert create_res.status_code == 201
    trip_data = create_res.json()["data"]
    trip_id = trip_data["id"]
    assert trip_data["destination"] == "Goa"
    assert trip_data["budget_amount"] == 80000.0

    # Get trip
    get_res = await async_client.get(f"/api/trips/{trip_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == trip_id

    # List trips
    list_res = await async_client.get("/api/trips", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # Update trip budget
    update_res = await async_client.patch(
        f"/api/trips/{trip_id}",
        json={"budget_amount": 65000.0},
        headers=auth_headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["budget_amount"] == 65000.0

    # Delete trip
    del_res = await async_client.delete(f"/api/trips/{trip_id}", headers=auth_headers)
    assert del_res.status_code == 200
