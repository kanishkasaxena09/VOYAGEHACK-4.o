import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_flights_hotels_activities_transfers(async_client: AsyncClient, auth_headers: dict):
    # Create trip
    trip_res = await async_client.post(
        "/api/trips",
        json={"title": "Goa Search Trip", "destination": "Goa", "origin": "DEL", "number_of_travellers": 2},
        headers=auth_headers
    )
    trip_id = trip_res.json()["data"]["id"]

    # 1. Search Flights
    f_res = await async_client.post(f"/api/trips/{trip_id}/search/flights", json={"passengers": 2}, headers=auth_headers)
    assert f_res.status_code == 200
    flights = f_res.json()["data"]
    assert len(flights) > 0
    assert flights[0]["category"] == "FLIGHT"
    assert flights[0]["available"] is True

    # 2. Search Hotels
    h_res = await async_client.post(f"/api/trips/{trip_id}/search/hotels", json={"guests": 2}, headers=auth_headers)
    assert h_res.status_code == 200
    hotels = h_res.json()["data"]
    assert len(hotels) > 0
    assert hotels[0]["category"] == "HOTEL"

    # 3. Search Activities
    a_res = await async_client.post(f"/api/trips/{trip_id}/search/activities", json={"participants": 2}, headers=auth_headers)
    assert a_res.status_code == 200
    activities = a_res.json()["data"]
    assert len(activities) > 0

    # 4. Search Transfers
    t_res = await async_client.post(f"/api/trips/{trip_id}/search/transfers", json={"passengers": 2}, headers=auth_headers)
    assert t_res.status_code == 200
    transfers = t_res.json()["data"]
    assert len(transfers) > 0

    # 5. Search All
    all_res = await async_client.post(f"/api/trips/{trip_id}/search/all", headers=auth_headers)
    assert all_res.status_code == 200
    all_data = all_res.json()["data"]
    assert len(all_data["flights"]) > 0
    assert len(all_data["hotels"]) > 0
