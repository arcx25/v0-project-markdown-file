"""Admin web routes - Server-side rendered admin panel."""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User, UserRole, VendorProfile, BuyerProfile, VerificationStatus
from app.models.lead import Lead, LeadStatus
from app.models.listing import SupportListing, ListingStatus
from app.services.lead_service import LeadService
from app.config import settings
from app.web.routes import get_template_context

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


async def get_admin_stats(db: AsyncSession) -> dict:
    """Get admin dashboard statistics."""
    pending_leads = (await db.execute(
        select(func.count()).select_from(Lead).where(Lead.status == LeadStatus.SUBMITTED)
    )).scalar() or 0
    
    pending_vendors = (await db.execute(
        select(func.count()).select_from(VendorProfile)
        .where(VendorProfile.verification_status == VerificationStatus.PENDING)
    )).scalar() or 0
    
    pending_listings = (await db.execute(
        select(func.count()).select_from(SupportListing)
        .where(SupportListing.status == ListingStatus.PENDING_REVIEW)
    )).scalar() or 0
    
    total_users = (await db.execute(
        select(func.count()).select_from(User)
    )).scalar() or 0
    
    return {
        "pending_leads": pending_leads,
        "pending_vendors": pending_vendors,
        "pending_listings": pending_listings,
        "total_users": total_users,
    }


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Admin dashboard overview."""
    stats = await get_admin_stats(db)
    
    return templates.TemplateResponse(
        "admin/dashboard.html",
        get_template_context(
            request,
            current_user=current_user,
            stats=stats,
            section="overview",
        )
    )


@router.get("/leads", response_class=HTMLResponse)
async def admin_leads(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Leads pending review."""
    stats = await get_admin_stats(db)
    
    result = await db.execute(
        select(Lead)
        .where(Lead.status == LeadStatus.SUBMITTED)
        .order_by(Lead.created_at.asc())
    )
    leads = result.scalars().all()
    
    for lead in leads:
        buyer_result = await db.execute(
            select(User).where(User.id == lead.buyer_id)
        )
        lead.buyer = buyer_result.scalar_one()
    
    return templates.TemplateResponse(
        "admin/leads.html",
        get_template_context(
            request,
            current_user=current_user,
            stats=stats,
            section="leads",
            leads=leads,
        )
    )


@router.post("/leads/{lead_id}/approve")
async def approve_lead(
    request: Request,
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Approve a lead for publication."""
    lead_service = LeadService(db)
    
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.status = LeadStatus.PUBLISHED
    lead.reviewed_by = current_user.id
    lead.reviewed_at = datetime.now(timezone.utc)
    lead.published_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return RedirectResponse("/admin/leads?success=approved", status_code=302)


@router.post("/leads/{lead_id}/reject")
async def reject_lead(
    request: Request,
    lead_id: UUID,
    reason: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Reject a lead."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead.status = LeadStatus.REJECTED
    lead.rejection_reason = reason
    lead.reviewed_by = current_user.id
    lead.reviewed_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    return RedirectResponse("/admin/leads?success=rejected", status_code=302)


@router.get("/vendors", response_class=HTMLResponse)
async def admin_vendors(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Vendors pending verification."""
    stats = await get_admin_stats(db)
    
    result = await db.execute(
        select(User, VendorProfile)
        .join(VendorProfile, User.id == VendorProfile.user_id)
        .where(VendorProfile.verification_status == VerificationStatus.PENDING)
        .order_by(User.created_at.asc())
    )
    vendors = result.all()
    
    return templates.TemplateResponse(
        "admin/vendors.html",
        get_template_context(
            request,
            current_user=current_user,
            stats=stats,
            section="vendors",
            vendors=vendors,
        )
    )


@router.post("/vendors/{vendor_id}/verify")
async def verify_vendor(
    request: Request,
    vendor_id: UUID,
    notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Verify a vendor."""
    result = await db.execute(
        select(VendorProfile).where(VendorProfile.user_id == vendor_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    profile.verification_status = VerificationStatus.VERIFIED
    profile.verification_notes = notes
    profile.verified_at = datetime.now(timezone.utc)
    profile.verified_by = current_user.id
    
    await db.commit()
    
    return RedirectResponse("/admin/vendors?success=verified", status_code=302)


@router.post("/vendors/{vendor_id}/reject")
async def reject_vendor(
    request: Request,
    vendor_id: UUID,
    reason: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Reject a vendor."""
    result = await db.execute(
        select(VendorProfile).where(VendorProfile.user_id == vendor_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Vendor profile not found")
    
    profile.verification_status = VerificationStatus.REJECTED
    profile.verification_notes = reason
    profile.verified_at = datetime.now(timezone.utc)
    profile.verified_by = current_user.id
    
    await db.commit()
    
    return RedirectResponse("/admin/vendors?success=rejected", status_code=302)



@router.get("/listings", response_class=HTMLResponse)
async def admin_listings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Listings pending review."""
    stats = await get_admin_stats(db)
    
    result = await db.execute(
        select(SupportListing)
        .where(SupportListing.status == ListingStatus.PENDING_REVIEW)
        .order_by(SupportListing.created_at.asc())
    )
    listings = result.scalars().all()
    
    for listing in listings:
        buyer_result = await db.execute(
            select(User).where(User.id == listing.buyer_id)
        )
        listing.buyer = buyer_result.scalar_one()
    
    return templates.TemplateResponse(
        "admin/listings.html",
        get_template_context(
            request,
            current_user=current_user,
            stats=stats,
            section="listings",
            listings=listings,
        )
    )



@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    q: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """User management."""
    stats = await get_admin_stats(db)
    
    page_size = 50
    query = select(User)
    
    if q:
        query = query.where(
            User.username.ilike(f"%{q}%") | 
            User.pgp_fingerprint.ilike(f"%{q}%")
        )
    
    if role:
        query = query.where(User.role == UserRole(role))
    
    if status == "active":
        query = query.where(User.is_active == True)
    elif status == "suspended":
        query = query.where(User.is_active == False)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return templates.TemplateResponse(
        "admin/users.html",
        get_template_context(
            request,
            current_user=current_user,
            stats=stats,
            section="users",
            users=users,
            search_query=q,
            role_filter=role,
            status_filter=status,
            page=page,
            total=total,
            total_pages=(total + page_size - 1) // page_size,
        )
    )


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Suspend a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot suspend admin")
    
    user.is_active = False
    
    if user.vendor_profile:
        user.vendor_profile.verification_status = VerificationStatus.SUSPENDED
    
    await db.commit()
    
    return RedirectResponse("/admin/users?success=suspended", status_code=302)


@router.post("/users/{user_id}/unsuspend")
async def unsuspend_user(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Unsuspend a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    
    if user.vendor_profile:
        user.vendor_profile.verification_status = VerificationStatus.PENDING
    
    await db.commit()
    
    return RedirectResponse("/admin/users?success=unsuspended", status_code=302)
