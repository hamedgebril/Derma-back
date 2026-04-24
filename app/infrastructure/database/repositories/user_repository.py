"""
Data access layer for user operations
"""
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.user import User

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, email: str, username: str, hashed_password: str) -> User:
        """Create new user"""
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            is_active=True
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info(f"Created user: {user.id} - {user.email}")
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update user password"""
        user = await self.get_by_id(user_id)
        if user:
            user.hashed_password = hashed_password
            await self.session.commit()
            logger.info(f"Updated password for user: {user_id}")
            return True
        return False
    
    async def deactivate(self, user_id: int) -> bool:
        """Deactivate user account"""
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = False
            await self.session.commit()
            logger.info(f"Deactivated user: {user_id}")
            return True
        return False
