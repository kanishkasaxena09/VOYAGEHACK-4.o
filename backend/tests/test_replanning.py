import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_partial_replanning_flow(async_client: AsyncClient, auth_headers: dict):
    # 1. Create initial trip
    trip_res = await async_client.post(
        "/api/trips",
        json={
            "title": "Replanning Demo Trip",
            "destination": "Goa",
            "origin": "DEL",
            "duration_days": 5,
            "number_of_travellers": 2,
            "budget_amount": 80000.0
        },
        headers=auth_headers
    )
    trip_id = trip_res.json()["data"]["id"]

    # 2. Generate initial itineraries
    gen_res = await async_client.post(f"/api/trips/{trip_id}/itinerary/generate", headers=auth_headers)
    assert gen_res.status_code == 200
    itins = gen_res.json()["data"]
    balanced_itin = next(i for i in itins if i["tier"] == "Balanced")
    original_cost = balanced_itin["total_estimated_cost"]

    # 3. Request partial replanning to reduce cost to ₹65,000
    replan_res = await async_client.post(
        f"/api/trips/{trip_id}/itinerary/replan",
        json={"target_budget": 65000.0, "change_hotel": True, "change_flight": True},
        headers=auth_headers
    )
    assert replan_res.status_code == 200
    replan_data = replan_res.json()["data"]
    assert replan_data["success"] is True
    assert "budget_target" in replan_data["modified_components"]
    assert replan_data["new_total"] < original_cost
    assert replan_data["new_total"] <= 70000.0
