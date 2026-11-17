import pytest
from httpx import AsyncClient
from app.services.cost_service import CostService
from app.services.pricing_service import PricingService


@pytest.mark.asyncio
async def test_deterministic_cost_engine_calculation():
    # Unit test cost calculation formula:
    # subtotal = flight + hotel + activity + transfer
    # taxes = subtotal * 5%
    # fees = 850
    # discount = 1000
    # total = subtotal + taxes + fees - discount
    res = CostService.calculate_totals(
        flight_cost=25000.0,
        hotel_cost=20000.0,
        activity_cost=8000.0,
        transfer_cost=4000.0
    )

    subtotal = 57000.0
    expected_tax = 2850.0  # 5%
    expected_fees = 850.0
    expected_discount = 1000.0
    expected_total = subtotal + expected_tax + expected_fees - expected_discount

    assert res["flight_cost"] == 25000.0
    assert res["hotel_cost"] == 20000.0
    assert res["taxes"] == expected_tax
    assert res["fees"] == expected_fees
    assert res["discounts"] == expected_discount
    assert res["total"] == expected_total


@pytest.mark.asyncio
async def test_price_validation_service():
    pricing_svc = PricingService()

    # Valid flight check
    val_resp = await pricing_svc.validate_component_price(
        category="FLIGHT",
        item_id="FL-GOA-101",
        expected_price=13500.0
    )
    assert val_resp.is_valid is True
    assert val_resp.available is True
    assert val_resp.price_changed is False

    # Price mismatch check
    val_mismatch = await pricing_svc.validate_component_price(
        category="FLIGHT",
        item_id="FL-GOA-101",
        expected_price=9000.0
    )
    assert val_mismatch.price_changed is True
    assert val_mismatch.is_valid is False


@pytest.mark.asyncio
async def test_pricing_endpoint_integration(async_client: AsyncClient, auth_headers: dict):
    trip_res = await async_client.post(
        "/api/trips",
        json={"title": "Cost Test Trip", "destination": "Goa", "number_of_travellers": 2},
        headers=auth_headers
    )
    trip_id = trip_res.json()["data"]["id"]

    cost_res = await async_client.get(f"/api/trips/{trip_id}/cost", headers=auth_headers)
    assert cost_res.status_code == 200
    data = cost_res.json()["data"]
    assert data["total"] > 0.0
    assert data["taxes"] > 0.0
    assert data["currency"] == "INR"
