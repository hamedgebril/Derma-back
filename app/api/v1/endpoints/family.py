"""
Family Members API endpoints
"""
import logging
from typing import Annotated, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.infrastructure.database.models.family_member import FamilyMember
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

# ===================== Schemas =====================

class FamilyMemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    relation: str = Field(..., pattern="^(self|spouse|child|parent|sibling|other)$")
    date_of_birth: date | None = None
    gender: str | None = Field(None, pattern="^(male|female|other)$")
    notes: str | None = Field(None, max_length=500)

class FamilyMemberUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    relation: str | None = Field(None, pattern="^(self|spouse|child|parent|sibling|other)$")
    date_of_birth: date | None = None
    gender: str | None = Field(None, pattern="^(male|female|other)$")
    notes: str | None = Field(None, max_length=500)

# ===================== Endpoints =====================

@router.get(
    "/members",
    response_model=List[dict],
    summary="Get all family members",
)
async def get_family_members(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        result = await db.execute(
            select(FamilyMember)
            .where(FamilyMember.user_id == user_id)
            .order_by(FamilyMember.created_at)
        )
        members = result.scalars().all()
        return [m.to_dict() for m in members]
    except Exception as e:
        logger.error(f"Error fetching family members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch family members"
        )


@router.post(
    "/members",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add family member",
)
async def add_family_member(
    data: FamilyMemberCreate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        result = await db.execute(
            select(FamilyMember).where(FamilyMember.user_id == user_id)
        )
        existing = result.scalars().all()
        if len(existing) >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 family members allowed per account"
            )

        member = FamilyMember(
            user_id=user_id,
            name=data.name,
            relation=data.relation,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            notes=data.notes,
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)

        logger.info(f"Family member added: {member.name} for user {user_id}")
        return member.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding family member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add family member"
        )


@router.put(
    "/members/{member_id}",
    response_model=dict,
    summary="Update family member",
)
async def update_family_member(
    member_id: int,
    data: FamilyMemberUpdate,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        result = await db.execute(
            select(FamilyMember).where(
                FamilyMember.id == member_id,
                FamilyMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family member not found"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(member, field, value)

        await db.commit()
        await db.refresh(member)
        logger.info(f"Family member {member_id} updated by user {user_id}")
        return member.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating family member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update family member"
        )


@router.delete(
    "/members/{member_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete family member",
)
async def delete_family_member(
    member_id: int,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        result = await db.execute(
            select(FamilyMember).where(
                FamilyMember.id == member_id,
                FamilyMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Family member not found"
            )

        await db.delete(member)
        await db.commit()

        logger.info(f"Family member {member_id} deleted by user {user_id}")
        return {"success": True, "message": "Family member deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting family member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete family member"
        )