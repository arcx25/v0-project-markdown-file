"""Secure messaging service with E2E PGP encryption."""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timezone

from app.models.message import Conversation, Message
from app.models.user import User
from app.models.lead import Lead
from app.services.pgp_service import PGPService


class MessageService:
    """Service for end-to-end encrypted messaging between buyers and vendors."""
    
    def __init__(self, pgp_service: PGPService):
        self.pgp = pgp_service
    
    async def get_conversation_by_id(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_user_conversations(
        self,
        db: AsyncSession,
        user_id: int
    ) -> List[Conversation]:
        """List all conversations for a user."""
        
        stmt = (
            select(Conversation)
            .where(
                or_(
                    Conversation.buyer_id == user_id,
                    Conversation.vendor_id == user_id
                )
            )
            .order_by(Conversation.last_message_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def send_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        sender_id: int,
        content: str,
        attachment_ids: Optional[List[int]] = None
    ) -> Tuple[bool, Optional[Message], Optional[str]]:
        """Send an encrypted message in a conversation."""
        
        # Get conversation
        conversation = await self.get_conversation_by_id(db, conversation_id)
        
        if not conversation:
            return False, None, "Conversation not found"
        
        if not conversation.is_active:
            return False, None, "Conversation is closed"
        
        # Verify sender is part of conversation
        if sender_id not in [conversation.buyer_id, conversation.vendor_id]:
            return False, None, "You are not part of this conversation"
        
        # Determine recipient
        recipient_id = (
            conversation.vendor_id 
            if sender_id == conversation.buyer_id 
            else conversation.buyer_id
        )
        
        # Get recipient's public key
        stmt = select(User).where(User.id == recipient_id)
        result = await db.execute(stmt)
        recipient = result.scalar_one_or_none()
        
        if not recipient:
            return False, None, "Recipient not found"
        
        # Encrypt message for recipient
        encrypted_content = self.pgp.encrypt_message(content, recipient.pgp_fingerprint)
        
        if not encrypted_content:
            return False, None, "Failed to encrypt message"
        
        # Create message
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            encrypted_content=encrypted_content,
            recipient_fingerprint=recipient.pgp_fingerprint,
            has_attachments=bool(attachment_ids),
            attachment_ids=str(attachment_ids) if attachment_ids else None
        )
        
        db.add(message)
        
        # Update conversation
        conversation.last_message_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(message)
        
        return True, message, None
    
    async def get_conversation_messages(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[bool, List[Message], Optional[str]]:
        """Get messages from a conversation."""
        
        # Verify user is part of conversation
        conversation = await self.get_conversation_by_id(db, conversation_id)
        
        if not conversation:
            return False, [], "Conversation not found"
        
        if user_id not in [conversation.buyer_id, conversation.vendor_id]:
            return False, [], "You are not part of this conversation"
        
        # Get messages
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        messages = list(result.scalars().all())
        
        # Reverse to chronological order
        messages.reverse()
        
        # Mark messages as read if user is recipient
        for message in messages:
            if message.sender_id != user_id and not message.read_at:
                message.read_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return True, messages, None
    
    async def mark_message_as_read(
        self,
        db: AsyncSession,
        message_id: int,
        user_id: int
    ) -> bool:
        """Mark a message as read."""
        
        stmt = select(Message).where(Message.id == message_id)
        result = await db.execute(stmt)
        message = result.scalar_one_or_none()
        
        if not message:
            return False
        
        # Get conversation to verify user is recipient
        conversation = await self.get_conversation_by_id(db, message.conversation_id)
        
        if not conversation:
            return False
        
        # Only recipient can mark as read
        if message.sender_id == user_id:
            return False
        
        if user_id not in [conversation.buyer_id, conversation.vendor_id]:
            return False
        
        message.read_at = datetime.now(timezone.utc)
        await db.commit()
        
        return True
    
    def decrypt_message_for_user(
        self,
        message: Message,
        user: User
    ) -> Optional[str]:
        """
        Attempt to decrypt a message for a user.
        Note: This requires the private key to be in the GPG keyring.
        In production, decryption would happen client-side.
        """
        
        # Check if user is the intended recipient
        if message.recipient_fingerprint != user.pgp_fingerprint:
            return None
        
        # Attempt decryption
        decrypted = self.pgp.decrypt_message(message.encrypted_content)
        
        return decrypted
