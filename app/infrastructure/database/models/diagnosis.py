"""
Diagnosis database model
"""
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.infrastructure.database.base import Base


class Diagnosis(Base):
    """Diagnosis record model"""
    
    __tablename__ = "diagnoses"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    family_member_id = Column(Integer, ForeignKey("family_members.id", ondelete="SET NULL"), nullable=True)  # ✅ جديد
    
    # Session tracking
    session_id = Column(String(36), unique=True, index=True, nullable=False)
    
    # Image information
    image_path = Column(String(512), nullable=False)
    image_quality_score = Column(Integer)  # 0-100
    image_quality_label = Column(String(50))  # Excellent, Good, Fair, Poor
    
    # Prediction results
    disease_type = Column(String(255), nullable=False, index=True)
    probability = Column(Float, nullable=False)
    confidence_percentage = Column(Float, nullable=False)
    
    # Additional data (JSON)
    all_predictions = Column(Text)  # JSON array of all predictions
    extra_metadata = Column(Text)  # JSON object with additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="diagnoses")
    family_member = relationship("FamilyMember", back_populates="diagnoses")  # ✅ جديد
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_disease_confidence', 'disease_type', 'confidence_percentage'),
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "family_member_id": self.family_member_id,  # ✅ جديد
            "family_member_name": self.family_member.name if self.family_member else None,  # ✅ جديد
            "session_id": self.session_id,
            "image_path": self.image_path,
            "image_quality": {
                "score": self.image_quality_score,
                "label": self.image_quality_label
            },
            "top_prediction": {
                "disease_type": self.disease_type,
                "probability": self.probability,
                "confidence_percentage": self.confidence_percentage
            },
            "all_predictions": json.loads(self.all_predictions) if self.all_predictions else [],
            "metadata": json.loads(self.extra_metadata) if self.extra_metadata else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return (
            f"<Diagnosis(id={self.id}, session={self.session_id}, "
            f"disease={self.disease_type}, confidence={self.confidence_percentage}%)>"
        )