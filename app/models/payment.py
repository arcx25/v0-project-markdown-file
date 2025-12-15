"""Payment and subscription models."""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class DepositStatus(str, enum.Enum):
    """Deposit status."""
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"


class Deposit(Base):
    """Monero deposit tracking."""
    __tablename__ = "deposits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Monero Details
    address = Column(String(95), unique=True, nullable=False, index=True)
    payment_id = Column(String(64), unique=True, nullable=False, index=True)
    expected_amount_atomic = Column(Numeric(20, 0), nullable=False)
    
    # Status
    status = Column(Enum(DepositStatus), default=DepositStatus.PENDING, nullable=False)
    confirmations = Column(Integer, default=0)
    
    # Purpose
    purpose = Column(String(100), nullable=False)  # e.g., "subscription", "listing_contribution"
    reference_id = Column(String(100))  # Related entity ID
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship("User")


class SubscriptionTier(str, enum.Enum):
    """Journalist subscription tiers."""
    FREE = "free"
    FREELANCER = "freelancer"
    OUTLET = "outlet"
    ENTERPRISE = "enterprise"


class Subscription(Base):
    """Journalist subscription."""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Subscription Details
    tier = Column(Enum(SubscriptionTier), nullable=False)
    
    # Payment
    amount_usd = Column(Integer, nullable=False)
    payment_method = Column(String(50), nullable=False)  # "monero" or "stripe"
    
    # Lifecycle
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, default=True, nullable=False)
    cancelled_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
