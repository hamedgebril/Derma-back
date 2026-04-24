"""
Data access layer for diagnosis operations
"""
import json
import logging
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.diagnosis import Diagnosis

logger = logging.getLogger(__name__)


class DiagnosisRepository:
    """Repository for diagnosis data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, data: dict) -> Diagnosis:
        """Create new diagnosis record"""
        # Convert all_predictions to JSON string
        if "all_predictions" in data and isinstance(data["all_predictions"], list):
            data["all_predictions"] = json.dumps(data["all_predictions"])
        
        # Convert metadata to JSON string
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["extra_metadata"] = json.dumps(data["metadata"])
            del data["metadata"]
        
        diagnosis = Diagnosis(**data)
        self.session.add(diagnosis)
        await self.session.commit()
        await self.session.refresh(diagnosis)
        
        logger.info(f"Created diagnosis: {diagnosis.id}")
        return diagnosis
    
    async def get_by_id(self, diagnosis_id: int) -> Optional[Diagnosis]:
        """Get diagnosis by ID"""
        result = await self.session.execute(
            select(Diagnosis).where(Diagnosis.id == diagnosis_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_session_id(self, session_id: str) -> Optional[Diagnosis]:
        """Get diagnosis by session ID"""
        result = await self.session.execute(
            select(Diagnosis).where(Diagnosis.session_id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Diagnosis]:
        """Get user's diagnosis history"""
        result = await self.session.execute(
            select(Diagnosis)
            .where(Diagnosis.user_id == user_id)
            .order_by(desc(Diagnosis.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def delete(self, diagnosis_id: int) -> bool:
        """Delete diagnosis record"""
        diagnosis = await self.get_by_id(diagnosis_id)
        if diagnosis:
            await self.session.delete(diagnosis)
            await self.session.commit()
            logger.info(f"Deleted diagnosis: {diagnosis_id}")
            return True
        return False
