"""Lead and matching models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class LeadCategory(str, enum.Enum):
    """Lead categories."""
    CORRUPTION = "corruption"
    CORPORATE_MISCONDUCT = "corporate_misconduct"
    GOVERNMENT_ABUSE = "government_abuse"
    ENVIRONMENTAL = "environmental"
    HUMAN_RIGHTS = "human_rights"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    OTHER = "other"


class LeadScope(str, enum.Enum):
    """Geographic or organizational scope."""
    LOCAL = "local"
    REGIONAL = "regional"
    NATIONAL = "national"
    INTERNATIONAL = "international"


class LeadStatus(str, enum.Enum):
    """Lead lifecycle status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    MATCHED = "matched"
    CLOSED = "closed"


class Lead(Base):
    """Buyer-submitted lead."""
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Content
    title = Column(String(500), nullable=False)
    category = Column(Enum(LeadCategory), nullable=False)
    scope = Column(Enum(LeadScope), nullable=False)
    summary = Column(Text, nullable=False)
    evidence_types = Column(JSON)  # List of evidence types available
    
    # Matching
    preferred_vendor_qualities = Column(Text)
    matched_vendor_id = Column(Integer, ForeignKey("users.id"))
    
    # Status
    status = Column(Enum(LeadStatus), default=LeadStatus.DRAFT, nullable=False)
    rejection_reason = Column(Text)
    
    # Moderation
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    published_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id])
    matched_vendor = relationship("User", foreign_keys=[matched_vendor_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    interests = relationship("LeadInterest", back_populates="lead")


class InterestStatus(str, enum.Enum):
    """Status of vendor interest."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class LeadInterest(Base):
    """Vendor interest in a lead."""
    __tablename__ = "lead_interests"
    
    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Content
    pitch = Column(Text, nullable=False)
    
    # Status
    status = Column(Enum(InterestStatus), default=InterestStatus.PENDING, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    responded_at = Column(DateTime(timezone=True))
    
    # Relationships
    lead = relationship("Lead", back_populates="interests")
    vendor = relationship("User")
