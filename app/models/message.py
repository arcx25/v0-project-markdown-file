"""Secure messaging models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Conversation(Base):
    """Encrypted conversation between buyer and vendor."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_message_at = Column(DateTime(timezone=True))
    
    # Relationships
    lead = relationship("Lead")
    buyer = relationship("User", foreign_keys=[buyer_id])
    vendor = relationship("User", foreign_keys=[vendor_id])
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    """End-to-end encrypted message."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Encrypted Content
    encrypted_content = Column(Text, nullable=False)  # PGP encrypted for recipient
    recipient_fingerprint = Column(String(40), nullable=False)
    
    # Attachments
    has_attachments = Column(Boolean, default=False, nullable=False)
    attachment_ids = Column(Text)  # JSON array of encrypted_media IDs
    
    # Status
    read_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
