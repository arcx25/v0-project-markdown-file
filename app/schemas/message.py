"""Message schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SendMessageRequest(BaseModel):
    """Send a message in a conversation."""
    content: str = Field(..., min_length=1, max_length=50000)
    attachment_ids: Optional[List[int]] = Field(default_factory=list)


class MessageResponse(BaseModel):
    """Message response."""
    id: int
    conversation_id: int
    sender_id: int
    sender_username: str
    encrypted_content: str
    has_attachments: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    # Decrypted content (only for recipient)
    decrypted_content: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: int
    lead_id: int
    lead_title: str
    source_id: int
    journalist_id: int
    other_party_username: str
    is_active: bool
    created_at: datetime
    last_message_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: List[ConversationResponse]
    total: int


class ConversationDetailResponse(BaseModel):
    """Conversation with messages."""
    conversation: ConversationResponse
    messages: List[MessageResponse]
