"""
Family Member database model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.infrastructure.database.base import Base


class FamilyMember(Base):
    """Family Member model - linked to a user account"""

    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    relation = Column(String(50), nullable=False)  # ✅ غيّرنا من relationship → relation
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="family_members")
    diagnoses = relationship("Diagnosis", back_populates="family_member", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FamilyMember(id={self.id}, name={self.name}, relation={self.relation})>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "relation": self.relation,  # ✅
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }