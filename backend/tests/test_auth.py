import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient):
    # Register
    reg_res = await async_client.post(
        "/api/auth/register",
        json={"email": "alice@travel.com", "password": "securepassword", "full_name": "Alice"}
    )
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert data["success"] is True
    assert data["data"]["email"] == "alice@travel.com"

    # Duplicate registration should fail
    dup_res = await async_client.post(
        "/api/auth/register",
        json={"email": "alice@travel.com", "password": "securepassword"}
    )
    assert dup_res.status_code == 422
    assert dup_res.json()["success"] is False

    # Login
    login_res = await async_client.post(
        "/api/auth/login",
        json={"email": "alice@travel.com", "password": "securepassword"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    assert token is not None

    # Get Me
    me_res = await async_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "alice@travel.com"
