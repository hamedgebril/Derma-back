"""
Authentication endpoints
"""
import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.infrastructure.database.models.user import User
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# ===================== Schemas =====================

class GoogleAuthRequest(BaseModel):
    email: str
    google_uid: str
    display_name: str | None = None
    photo_url: str | None = None

class UpdateProfileRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

class DeleteAccountRequest(BaseModel):
    confirm_text: str

# ===================== Endpoints =====================

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    try:
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        result = await db.execute(select(User).where(User.username == user_data.username))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")

        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            is_active=True
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"New user registered: {new_user.email}")
        return UserResponse.model_validate(new_user)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user account")


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    try:
        result = await db.execute(select(User).where(User.email == credentials.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=403, detail="User account is inactive")

        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        logger.info(f"User logged in: {user.email}")
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/google", response_model=Token)
async def google_auth(
    data: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    Google Sign-In:
    - لو الـ user موجود بالـ email → login مباشرة
    - لو مش موجود → إنشاء account جديد
    """
    try:
        # ✅ شوف لو الـ user موجود
        result = await db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user:
            # ✅ إنشاء username من الـ display_name أو الـ email
            base_username = (
                data.display_name.replace(" ", "_").lower()
                if data.display_name
                else data.email.split('@')[0]
            )

            # تأكد إن الـ username مش موجود - لو موجود ضيف رقم
            username = base_username
            counter = 1
            while True:
                result = await db.execute(select(User).where(User.username == username))
                if not result.scalar_one_or_none():
                    break
                username = f"{base_username}_{counter}"
                counter += 1

            # ✅ إنشاء الـ user - بنحفظ google_uid كـ hashed_password
            # (Google users مش محتاجين password حقيقي)
            user = User(
                email=data.email,
                username=username,
                hashed_password=get_password_hash(data.google_uid),
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"New Google user created: {user.email} (id={user.id})")
        else:
            logger.info(f"Google user logged in: {user.email} (id={user.id})")

        # ✅ إنشاء JWT token حقيقي بالـ user.id الفعلي
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return Token(access_token=access_token, token_type="bearer")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Google authentication failed")


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UpdateProfileRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = data.name
    await db.commit()
    await db.refresh(user)
    logger.info(f"Profile updated for user {user_id}")
    return UserResponse.model_validate(user)


@router.put("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.hashed_password = get_password_hash(data.new_password)
    await db.commit()
    logger.info(f"Password changed for user {user_id}")
    return {"success": True, "message": "Password changed successfully"}


@router.delete("/delete-account")
async def delete_account(
    data: DeleteAccountRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if data.confirm_text != "DELETE":
        raise HTTPException(status_code=400, detail="Please type DELETE to confirm")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    logger.info(f"Account deleted for user {user_id}")
    return {"success": True, "message": "Account deleted successfully"}