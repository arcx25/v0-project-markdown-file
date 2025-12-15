"""Dashboard web routes - Server-side rendered dashboards."""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, date

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole, VendorProfile, BuyerProfile
from app.models.lead import Lead, LeadStatus, LeadCategory, LeadInterest, InterestStatus
from app.models.listing import SupportListing, ListingStatus, ListingCategory, SupportTier
from app.models.message import Conversation
from app.services.monero_service import monero_service
from app.services.message_service import MessageService
from app.services.lead_service import LeadService
from app.services.listing_service import ListingService
from app.config import settings
from app.web.routes import get_template_context

router = APIRouter(prefix="/dashboard")
templates = Jinja2Templates(directory="app/templates")


async def get_dashboard_stats(db: AsyncSession, user: User) -> dict:
    """Get dashboard statistics for a user."""
    stats = {"open_conversations": 0}
    
    if user.role == UserRole.BUYER:
        # Active leads
        leads_result = await db.execute(
            select(func.count())
            .select_from(Lead)
            .where(Lead.buyer_id == user.id)
            .where(Lead.status.in_([
                LeadStatus.PUBLISHED, LeadStatus.MATCHED, LeadStatus.IN_PROGRESS
            ]))
        )
        stats["active_leads"] = leads_result.scalar() or 0
        
        # Pending interests on buyer's leads
        interests_result = await db.execute(
            select(func.count())
            .select_from(LeadInterest)
            .join(Lead, LeadInterest.lead_id == Lead.id)
            .where(Lead.buyer_id == user.id)
            .where(LeadInterest.status == InterestStatus.PENDING)
        )
        stats["pending_interests"] = interests_result.scalar() or 0
        
        # Total raised
        listings_result = await db.execute(
            select(func.sum(SupportListing.total_raised_atomic))
            .where(SupportListing.buyer_id == user.id)
        )
        total_atomic = listings_result.scalar() or 0
        stats["total_raised_xmr"] = f"{monero_service.atomic_to_xmr(total_atomic):.6f}"
        
    else:  # Vendor
        # Active interests
        interests_result = await db.execute(
            select(func.count())
            .select_from(LeadInterest)
            .where(LeadInterest.vendor_id == user.id)
            .where(LeadInterest.status == InterestStatus.PENDING)
        )
        stats["active_interests"] = interests_result.scalar() or 0
        
        # Accepted interests
        accepted_result = await db.execute(
            select(func.count())
            .select_from(LeadInterest)
            .where(LeadInterest.vendor_id == user.id)
            .where(LeadInterest.status == InterestStatus.ACCEPTED)
        )
        stats["accepted_interests"] = accepted_result.scalar() or 0
        
        # Subscription tier
        if user.vendor_profile:
            stats["subscription_tier"] = user.vendor_profile.subscription_tier
        else:
            stats["subscription_tier"] = "free"
    
    # Open conversations (both roles)
    conv_result = await db.execute(
        select(func.count())
        .select_from(Conversation)
        .where(or_(
            Conversation.buyer_id == user.id,
            Conversation.vendor_id == user.id,
        ))
        .where(Conversation.closed_at.is_(None))
    )
    stats["open_conversations"] = conv_result.scalar() or 0
    
    return stats


async def get_unread_count(db: AsyncSession, user: User) -> int:
    """Get unread message count."""
    message_service = MessageService(db)
    return await message_service.get_unread_count(user)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def dashboard_overview(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dashboard overview page."""
    stats = await get_dashboard_stats(db, current_user)
    unread_count = await get_unread_count(db, current_user)
    
    return templates.TemplateResponse(
        "dashboard/index.html",
        get_template_context(
            request,
            section="overview",
            current_user=current_user,
            stats=stats,
            unread_count=unread_count,
            profile=current_user.vendor_profile,
            buyer_profile=current_user.buyer_profile,
        )
    )
