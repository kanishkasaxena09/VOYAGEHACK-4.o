from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db
from app.core.exceptions import UnauthorizedException, ValidationException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from app.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == user_in.email)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise ValidationException("An account with this email address already exists.")

    hashed_pw = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_pw,
        full_name=user_in.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return APIResponse.ok(
        data=UserResponse.model_validate(user),
        message="User registered successfully."
    )


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == credentials.email)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise UnauthorizedException("Incorrect email or password.")

    if not user.is_active:
        raise UnauthorizedException("User account is disabled.")

    token = create_access_token(user.id)
    return APIResponse.ok(
        data=TokenResponse(access_token=token, expires_in_minutes=120),
        message="Login successful."
    )


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(user: User = Depends(get_current_user)):
    return APIResponse.ok(
        data=UserResponse.model_validate(user),
        message="User profile retrieved."
    )
