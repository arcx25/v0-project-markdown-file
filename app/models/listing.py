"""Support listing models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean, Numeric, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class ListingCategory(str, enum.Enum):
    """Support listing categories."""
    INVESTIGATION = "investigation"
    LEGAL_DEFENSE = "legal_defense"
    RELOCATION = "relocation"
    MEDICAL = "medical"
    GENERAL_SUPPORT = "general_support"


class ListingStatus(str, enum.Enum):
    """Listing lifecycle status."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class SupportListing(Base):
    """Public support listing created by buyers."""
    __tablename__ = "support_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Identity
    title = Column(String(500), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(Enum(ListingCategory), nullable=False)
    
    # Content
    story = Column(Text, nullable=False)
    goals = Column(Text, nullable=False)
    use_of_funds = Column(Text)
    
    # Goals
    target_amount_usd = Column(Integer)
    current_amount_usd = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(ListingStatus), default=ListingStatus.DRAFT, nullable=False)
    rejection_reason = Column(Text)
    
    # Moderation
    reviewed_by_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    buyer = relationship("User")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    tiers = relationship("SupportTier", back_populates="listing", order_by="SupportTier.amount_usd")
    contributions = relationship("SupportContribution", back_populates="listing")
    supporter_wall = relationship("SupporterWallEntry", back_populates="listing", order_by="SupporterWallEntry.created_at.desc()")
    updates = relationship("ListingUpdate", back_populates="listing", order_by="ListingUpdate.created_at.desc()")


class SupportTier(Base):
    """Contribution tier with perks."""
    __tablename__ = "support_tiers"
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("support_listings.id"), nullable=False, index=True)
    
    # Tier Details
    name = Column(String(100), nullable=False)
    amount_usd = Column(Integer, nullable=False)
    description = Column(Text)
    perks = Column(JSON)  # List of perks
    
    # Limits
    max_supporters = Column(Integer)
    current_supporters = Column(Integer, default=0)
    
    # Display
    display_order = Column(Integer, default=0)
    
    # Relationships
    listing = relationship("SupportListing", back_populates="tiers")


class SupportContribution(Base):
    """Anonymous contribution to a listing."""
    __tablename__ = "support_contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("support_listings.id"), nullable=False, index=True)
    tier_id = Column(Integer, ForeignKey("support_tiers.id"))
    
    # Payment
    amount_xmr_atomic = Column(Numeric(20, 0), nullable=False)
    amount_usd_at_contribution = Column(Integer)
    monero_address = Column(String(95), unique=True, nullable=False)
    payment_id = Column(String(64), unique=True, nullable=False)
    
    # Status
    confirmed = Column(Boolean, default=False, nullable=False)
    confirmations = Column(Integer, default=0)
    confirmed_at = Column(DateTime(timezone=True))
    
    # Supporter Display
    display_on_wall = Column(Boolean, default=True, nullable=False)
    supporter_display_name = Column(String(100))
    supporter_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    listing = relationship("SupportListing", back_populates="contributions")
    tier = relationship("SupportTier")


class SupporterWallEntry(Base):
    """Public supporter wall entry."""
    __tablename__ = "supporter_wall"
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("support_listings.id"), nullable=False, index=True)
    contribution_id = Column(Integer, ForeignKey("support_contributions.id"), unique=True, nullable=False)
    
    # Display
    display_name = Column(String(100), nullable=False)
    tier_name = Column(String(100))
    amount_display = Column(String(50))  # e.g., "$50-$100"
    message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    listing = relationship("SupportListing", back_populates="supporter_wall")
    contribution = relationship("SupportContribution")


class ListingUpdate(Base):
    """Progress update posted by buyer."""
    __tablename__ = "listing_updates"
    
    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("support_listings.id"), nullable=False, index=True)
    
    # Content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    listing = relationship("SupportListing", back_populates="updates")
