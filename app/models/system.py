"""System and administrative models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class AuditLog(Base):
    """Audit trail for security-sensitive actions."""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Action
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100))
    
    # Details
    details = Column(JSON)
    
    # Context
    circuit_hash = Column(String(64))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class RateLimit(Base):
    """Rate limit tracking."""
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True)
    
    # Key (user_id, circuit_hash, or endpoint)
    key = Column(String(255), unique=True, nullable=False, index=True)
    
    # Counts
    count = Column(Integer, default=0, nullable=False)
    
    # Window
    window_start = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)


class EncryptedMedia(Base):
    """Encrypted file storage metadata."""
    __tablename__ = "encrypted_media"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File Details
    filename = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    
    # Storage
    storage_path = Column(String(1000), unique=True, nullable=False)
    encryption_key_fingerprint = Column(String(40), nullable=False)
    
    # Context
    context_type = Column(String(100))  # "message_attachment", "profile_image", etc.
    context_id = Column(String(100))
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    owner = relationship("User")
