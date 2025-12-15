"""Payment and subscription models."""

from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, Numeric, Text
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


class DepositPurpose(str, enum.Enum):
    """Purpose for deposit."""
    SUBSCRIPTION = "subscription"
    LISTING_CONTRIBUTION = "listing_contribution"
    GENERAL = "general"


class Deposit(Base):
    """Monero deposit tracking."""
    __tablename__ = "deposits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Monero Details
    address = Column(String(95), unique=True, nullable=False, index=True)
    payment_id = Column(String(64), unique=True, nullable=False, index=True)
    expected_amount_atomic = Column(Numeric(20, 0), nullable=False)
    received_amount_atomic = Column(Numeric(20, 0), default=0)
    
    # Status
    status = Column(Enum(DepositStatus), default=DepositStatus.PENDING, nullable=False)
    confirmations = Column(Integer, default=0)
    
    # Purpose
    purpose = Column(Enum(DepositPurpose), nullable=False)
    reference_id = Column(String(100))  # Related entity ID
    
    # QR Code
    qr_code_base64 = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    confirmed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship("User")


class SubscriptionTier(str, enum.Enum):
    """Vendor subscription tiers."""
    FREE = "free"
    FREELANCER = "freelancer"
    OUTLET = "outlet"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRING = "expiring"
    GRACE_PERIOD = "grace_period"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Subscription(Base):
    """Vendor subscription."""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Subscription Details
    tier = Column(Enum(SubscriptionTier), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False, index=True)
    
    # Payment
    price_usd_cents = Column(Integer, nullable=False)
    price_xmr_atomic = Column(Numeric(20, 0))
    payment_method = Column(String(50), nullable=False)  # "xmr" or "stripe"
    payment_reference = Column(String(100))  # Deposit ID or Stripe session ID
    
    # Lifecycle
    started_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    auto_renew = Column(Boolean, default=True, nullable=False)
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    
    # Limits tracking
    interests_this_month = Column(Integer, default=0)
    conversations_active = Column(Integer, default=0)
    team_members_count = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User")
