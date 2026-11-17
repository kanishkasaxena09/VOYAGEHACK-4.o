import uuid
from typing import AsyncGenerator
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ForbiddenException, ResourceNotFoundException, UnauthorizedException
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User
from app.models.trip import Trip

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise UnauthorizedException("Authentication token is missing.")

    payload = decode_access_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing subject.")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user ID in token.")

    stmt = select(User).where(User.id == user_uuid)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user:
        raise UnauthorizedException("User not found.")
    if not user.is_active:
        raise UnauthorizedException("User account is inactive.")

    return user


async def get_user_trip(
    trip_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Trip:
    """Ensures trip exists and caller owns the trip."""
    stmt = select(Trip).where(Trip.id == trip_id)
    res = await db.execute(stmt)
    trip = res.scalars().first()

    if not trip:
        raise ResourceNotFoundException("Trip", trip_id)
    if trip.user_id != user.id:
        raise ForbiddenException("You do not have access to this trip.")

    return trip
