import pytest
from httpx import AsyncClient
from app.agents.destination_agent import DestinationAgent
from app.agents.itinerary_agent import ItineraryAgent
from app.agents.preference_agent import PreferenceAgent
from app.models.trip import Trip


@pytest.mark.asyncio
async def test_preference_agent_extraction():
    msg = "I want a 5-day trip for 2 people in December. My budget is ₹80,000. I like beaches, food and relaxed sightseeing. I don't want expensive hotels."
    intent = await PreferenceAgent.extract_preferences(msg)

    assert intent.duration_days == 5
    assert intent.number_of_travellers == 2
    assert intent.budget == 80000.0
    assert "beaches" in intent.interests
    assert "food" in intent.interests
    assert intent.pace == "relaxed"


@pytest.mark.asyncio
async def test_destination_agent_recommendations():
    trip = Trip(
        destination="Goa",
        budget_amount=80000.0,
        budget_currency="INR",
        interests=["beaches", "food", "relaxed"]
    )
    recs = await DestinationAgent.discover_destinations(trip, max_recommendations=3)
    assert len(recs) == 3
    # Goa should be top recommendation with high fit score
    assert recs[0].destination == "Goa"
    assert recs[0].fit_score >= 85
    assert len(recs[0].why_it_fits) > 0


@pytest.mark.asyncio
async def test_itinerary_agent_variants():
    trip = Trip(
        destination="Goa",
        duration_days=5,
        number_of_travellers=2,
        budget_amount=80000.0
    )
    variants = ItineraryAgent.generate_itineraries(trip)
    assert len(variants) == 3
    tiers = [v["tier"] for v in variants]
    assert "Budget" in tiers
    assert "Balanced" in tiers
    assert "Premium" in tiers

    # Check 5 days structure
    balanced = next(v for v in variants if v["tier"] == "Balanced")
    assert len(balanced["items"]) == 5
    assert balanced["total_estimated_cost"] > 0.0


@pytest.mark.asyncio
async def test_chat_endpoint_langgraph_flow(async_client: AsyncClient, auth_headers: dict):
    # Create fresh trip
    trip_res = await async_client.post("/api/trips", json={"title": "Demo Trip"}, headers=auth_headers)
    trip_id = trip_res.json()["data"]["id"]

    # Step 1: Initial user intent
    chat_res1 = await async_client.post(
        f"/api/trips/{trip_id}/chat",
        json={"message": "I want a 5-day trip for two people in December. My budget is ₹80,000. We like beaches and food."},
        headers=auth_headers
    )
    assert chat_res1.status_code == 200
    data1 = chat_res1.json()["data"]
    assert "reply" in data1
    assert data1["trip_id"] == trip_id

    # Step 2: User chooses Goa
    chat_res2 = await async_client.post(
        f"/api/trips/{trip_id}/chat",
        json={"message": "I choose Goa. December 10-14."},
        headers=auth_headers
    )
    assert chat_res2.status_code == 200
    data2 = chat_res2.json()["data"]
    assert "Goa" in data2["reply"]
    assert data2["itineraries"] is not None

    # Step 3: Check conversation history
    conv_res = await async_client.get(f"/api/trips/{trip_id}/conversation", headers=auth_headers)
    assert conv_res.status_code == 200
    messages = conv_res.json()["data"]["messages"]
    assert len(messages) >= 4  # 2 user msgs + 2 agent replies
