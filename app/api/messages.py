"""Messaging API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_pgp_service
from app.services.message_service import MessageService
from app.services.pgp_service import PGPService
from app.models.user import User
from app.models.lead import Lead
from app.schemas.message import (
    SendMessageRequest,
    MessageResponse,
    ConversationResponse,
    ConversationListResponse,
    ConversationDetailResponse,
)

router = APIRouter(prefix="/api/conversations", tags=["messages"])


async def get_message_service(pgp: PGPService = Depends(get_pgp_service)) -> MessageService:
    """Dependency for message service."""
    return MessageService(pgp)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """List all conversations for current user."""
    
    conversations = await message_service.list_user_conversations(db, current_user.id)
    
    enriched = []
    for conv in conversations:
        stmt = select(Lead).where(Lead.id == conv.lead_id)
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()
        
        other_party_id = conv.vendor_id if conv.buyer_id == current_user.id else conv.buyer_id
        stmt = select(User).where(User.id == other_party_id)
        result = await db.execute(stmt)
        other_party = result.scalar_one_or_none()
        
        enriched.append(ConversationResponse(
            id=conv.id,
            lead_id=conv.lead_id,
            lead_title=lead.title if lead else "Unknown Lead",
            buyer_id=conv.buyer_id,
            vendor_id=conv.vendor_id,
            other_party_username=other_party.username if other_party else "Unknown",
            is_active=conv.is_active,
            created_at=conv.created_at,
            last_message_at=conv.last_message_at
        ))
    
    return ConversationListResponse(
        conversations=enriched,
        total=len(enriched)
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """Get a conversation with messages."""
    
    conversation = await message_service.get_conversation_by_id(db, conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if current_user.id not in [conversation.buyer_id, conversation.vendor_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not part of this conversation"
        )
    
    # Get messages
    skip = (page - 1) * page_size
    success, messages, error = await message_service.get_conversation_messages(
        db,
        conversation_id,
        current_user.id,
        skip=skip,
        limit=page_size
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Get lead and other party info
    stmt = select(Lead).where(Lead.id == conversation.lead_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()
    
    other_party_id = conversation.vendor_id if conversation.buyer_id == current_user.id else conversation.buyer_id
    stmt = select(User).where(User.id == other_party_id)
    result = await db.execute(stmt)
    other_party = result.scalar_one_or_none()
    
    # Format conversation
    conv_response = ConversationResponse(
        id=conversation.id,
        lead_id=conversation.lead_id,
        lead_title=lead.title if lead else "Unknown Lead",
        buyer_id=conversation.buyer_id,
        vendor_id=conversation.vendor_id,
        other_party_username=other_party.username if other_party else "Unknown",
        is_active=conversation.is_active,
        created_at=conversation.created_at,
        last_message_at=conversation.last_message_at
    )
    
    # Format messages
    message_responses = []
    for message in messages:
        stmt = select(User).where(User.id == message.sender_id)
        result = await db.execute(stmt)
        sender = result.scalar_one_or_none()
        
        # Attempt to decrypt if user is recipient
        decrypted_content = None
        if message.sender_id != current_user.id:
            # In production, decryption happens client-side
            # This is for demonstration purposes only
            decrypted_content = "[Encrypted message - decrypt with your private key]"
        
        message_responses.append(MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            sender_username=sender.username if sender else "Unknown",
            encrypted_content=message.encrypted_content,
            has_attachments=message.has_attachments,
            read_at=message.read_at,
            created_at=message.created_at,
            decrypted_content=decrypted_content
        ))
    
    return ConversationDetailResponse(
        conversation=conv_response,
        messages=message_responses
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    message_data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """Send a message in a conversation."""
    
    success, message, error = await message_service.send_message(
        db,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=message_data.content,
        attachment_ids=message_data.attachment_ids
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Get sender info
    stmt = select(User).where(User.id == current_user.id)
    result = await db.execute(stmt)
    sender = result.scalar_one_or_none()
    
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        sender_id=message.sender_id,
        sender_username=sender.username if sender else current_user.username,
        encrypted_content=message.encrypted_content,
        has_attachments=message.has_attachments,
        read_at=message.read_at,
        created_at=message.created_at,
        decrypted_content=message_data.content  # Echo back for sender
    )


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service)
):
    """Get messages from a conversation."""
    
    skip = (page - 1) * page_size
    success, messages, error = await message_service.get_conversation_messages(
        db,
        conversation_id,
        current_user.id,
        skip=skip,
        limit=page_size
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Format messages
    message_responses = []
    for message in messages:
        stmt = select(User).where(User.id == message.sender_id)
        result = await db.execute(stmt)
        sender = result.scalar_one_or_none()
        
        decrypted_content = None
        if message.sender_id != current_user.id:
            decrypted_content = "[Encrypted message - decrypt with your private key]"
        
        message_responses.append(MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            sender_username=sender.username if sender else "Unknown",
            encrypted_content=message.encrypted_content,
            has_attachments=message.has_attachments,
            read_at=message.read_at,
            created_at=message.created_at,
            decrypted_content=decrypted_content
        ))
    
    return message_responses
