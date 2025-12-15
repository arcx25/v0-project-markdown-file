"""Admin API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.services.lead_service import LeadService
from app.models.user import User, JournalistProfile, VerificationStatus
from app.models.lead import Lead, LeadStatus
from app.models.listing import SupportListing, ListingStatus
from app.schemas.admin import (
    PendingLeadResponse,
    ApproveLeadRequest,
    RejectLeadRequest,
    PendingJournalistResponse,
    VerifyJournalistRequest,
    PendingListingResponse,
    UserManagementResponse,
    SuspendUserRequest,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def get_lead_service() -> LeadService:
    """Dependency for lead service."""
    return LeadService()


@router.get("/leads/pending", response_model=List[PendingLeadResponse])
async def get_pending_leads(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all pending leads for review."""
    
    stmt = (
        select(Lead, User)
        .join(User, Lead.source_id == User.id)
        .where(Lead.status == LeadStatus.PENDING_REVIEW)
        .order_by(Lead.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        PendingLeadResponse(
            id=lead.id,
            source_id=lead.source_id,
            source_username=user.username,
            title=lead.title,
            category=lead.category.value,
            scope=lead.scope.value,
            summary=lead.summary,
            created_at=lead.created_at
        )
        for lead, user in rows
    ]


@router.post("/leads/{lead_id}/approve")
async def approve_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Approve a lead."""
    
    lead = await lead_service.get_lead_by_id(db, lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    try:
        approved_lead = await lead_service.approve_lead(db, lead, current_user.id)
        return {"message": "Lead approved", "lead_id": approved_lead.id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/leads/{lead_id}/reject")
async def reject_lead(
    lead_id: int,
    reject_data: RejectLeadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Reject a lead."""
    
    lead = await lead_service.get_lead_by_id(db, lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    try:
        rejected_lead = await lead_service.reject_lead(
            db, lead, current_user.id, reject_data.reason
        )
        return {"message": "Lead rejected", "lead_id": rejected_lead.id}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/journalists/pending", response_model=List[PendingJournalistResponse])
async def get_pending_journalists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all pending journalist verifications."""
    
    stmt = (
        select(User, JournalistProfile)
        .join(JournalistProfile, User.id == JournalistProfile.user_id)
        .where(JournalistProfile.verification_status == VerificationStatus.PENDING)
        .order_by(User.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        PendingJournalistResponse(
            id=profile.id,
            user_id=user.id,
            username=user.username,
            organization=profile.organization,
            position=profile.position,
            website=profile.website,
            bio=profile.bio,
            created_at=user.created_at
        )
        for user, profile in rows
    ]


@router.post("/journalists/{journalist_id}/verify")
async def verify_journalist(
    journalist_id: int,
    verify_data: VerifyJournalistRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Verify a journalist."""
    
    from datetime import datetime, timezone
    
    stmt = select(JournalistProfile).where(JournalistProfile.user_id == journalist_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Journalist profile not found"
        )
    
    profile.verification_status = VerificationStatus.VERIFIED
    profile.verification_notes = verify_data.notes
    profile.verified_at = datetime.now(timezone.utc)
    profile.verified_by_id = current_user.id
    
    await db.commit()
    
    return {"message": "Journalist verified", "journalist_id": journalist_id}


@router.get("/listings/pending", response_model=List[PendingListingResponse])
async def get_pending_listings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Get all pending listings for review."""
    
    stmt = (
        select(SupportListing, User)
        .join(User, SupportListing.source_id == User.id)
        .where(SupportListing.status == ListingStatus.PENDING_REVIEW)
        .order_by(SupportListing.created_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        PendingListingResponse(
            id=listing.id,
            source_id=listing.source_id,
            source_username=user.username,
            title=listing.title,
            slug=listing.slug,
            category=listing.category.value,
            story=listing.story,
            created_at=listing.created_at
        )
        for listing, user in rows
    ]


@router.post("/listings/{listing_id}/approve")
async def approve_listing(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Approve a listing."""
    
    from datetime import datetime, timezone
    
    stmt = select(SupportListing).where(SupportListing.id == listing_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    if listing.status != ListingStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending listings can be approved"
        )
    
    listing.status = ListingStatus.ACTIVE
    listing.reviewed_by_id = current_user.id
    listing.reviewed_at = datetime.now(timezone.utc)
    listing.published_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return {"message": "Listing approved", "listing_id": listing_id}


@router.get("/users", response_model=List[UserManagementResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """List all users for management."""
    
    skip = (page - 1) * page_size
    
    stmt = (
        select(User)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        UserManagementResponse(
            id=user.id,
            username=user.username,
            role=user.role.value,
            is_active=user.is_active,
            is_suspended=user.is_suspended,
            created_at=user.created_at,
            last_login_at=user.last_login_at
        )
        for user in users
    ]


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    suspend_data: SuspendUserRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Suspend a user."""
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_suspended = True
    user.suspension_reason = suspend_data.reason
    
    await db.commit()
    
    return {"message": "User suspended", "user_id": user_id}


@router.post("/users/{user_id}/unsuspend")
async def unsuspend_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Unsuspend a user."""
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_suspended = False
    user.suspension_reason = None
    
    await db.commit()
    
    return {"message": "User unsuspended", "user_id": user_id}
