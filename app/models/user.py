"""User and authentication models."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles."""
    BUYER = "buyer"
    VENDOR = "vendor"
    ADMIN = "admin"


class User(Base):
    """User account with PGP-based authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False)
    
    # PGP Identity
    pgp_fingerprint = Column(String(40), unique=True, nullable=False, index=True)
    pgp_public_key = Column(Text, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)
    suspension_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships
    vendor_profile = relationship("VendorProfile", back_populates="user", uselist=False)
    buyer_profile = relationship("BuyerProfile", back_populates="user", uselist=False)
    sessions = relationship("Session", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class VerificationStatus(str, enum.Enum):
    """Vendor verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class VendorProfile(Base):
    """Extended profile for vendors."""
    __tablename__ = "vendor_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Professional Info
    organization = Column(String(255))
    position = Column(String(255))
    website = Column(String(500))
    bio = Column(Text)
    
    # Verification
    verification_status = Column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False
    )
    verification_notes = Column(Text)
    verified_at = Column(DateTime(timezone=True))
    verified_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Subscription
    subscription_tier = Column(String(50))  # free, professional, business, enterprise
    
    # Relationships
    user = relationship("User", back_populates="vendor_profile")
    verified_by = relationship("User", foreign_keys=[verified_by_id])


class BuyerProfile(Base):
    """Extended profile for buyers."""
    __tablename__ = "buyer_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Identity
    anonymous_alias = Column(String(100))
    
    # Trust Metrics
    trust_score = Column(Integer, default=0)
    leads_published = Column(Integer, default=0)
    conversations_completed = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="buyer_profile")


class AuthChallenge(Base):
    """PGP authentication challenges."""
    __tablename__ = "auth_challenges"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False, index=True)
    challenge_text = Column(String(128), nullable=False)
    challenge_hash = Column(String(128), nullable=False, unique=True)
    
    # Security
    attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True))
    
    # Tracking
    circuit_hash = Column(String(64), index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)


class Session(Base):
    """User sessions with circuit binding."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Session Identity
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    circuit_hash = Column(String(64), index=True)
    
    # Lifecycle
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
