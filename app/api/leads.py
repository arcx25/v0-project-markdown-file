"""Lead API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user, get_current_buyer, get_current_vendor, get_current_admin
from app.services.lead_service import LeadService
from app.models.user import User, VendorProfile
from app.models.lead import Lead
from app.schemas.lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadListResponse,
    LeadInterestCreate,
    LeadInterestResponse,
    AcceptVendorRequest,
)

router = APIRouter(prefix="/api/leads", tags=["leads"])


async def get_lead_service() -> LeadService:
    """Dependency for lead service."""
    return LeadService()


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Create a new lead (buyer only)."""
    
    lead = await lead_service.create_lead(
        db,
        buyer_id=current_user.id,
        title=lead_data.title,
        category=lead_data.category,
        scope=lead_data.scope,
        summary=lead_data.summary,
        evidence_types=lead_data.evidence_types,
        preferred_vendor_qualities=lead_data.preferred_vendor_qualities
    )
    
    return lead


@router.get("", response_model=LeadListResponse)
async def list_leads(
    category: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_vendor),
    lead_service: LeadService = Depends(get_lead_service)
):
    """List active leads (vendor only)."""
    
    skip = (page - 1) * page_size
    leads, total = await lead_service.list_active_leads(
        db,
        category=category,
        scope=scope,
        skip=skip,
        limit=page_size
    )
    
    return LeadListResponse(
        leads=leads,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/my-leads", response_model=LeadListResponse)
async def list_my_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
    lead_service: LeadService = Depends(get_lead_service)
):
    """List leads created by current buyer."""
    
    skip = (page - 1) * page_size
    leads, total = await lead_service.list_buyer_leads(
        db,
        buyer_id=current_user.id,
        skip=skip,
        limit=page_size
    )
    
    return LeadListResponse(
        leads=leads,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Get a specific lead."""
    
    lead = await lead_service.get_lead_by_id(db, lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead.buyer_id != current_user.id and current_user.role.value != "admin":
        if current_user.role.value != "vendor" or lead.status.value != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: int,
    lead_data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Update a lead (buyer only, draft status)."""
    
    lead = await lead_service.get_lead_by_id(db, lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own leads"
        )
    
    if lead.status.value != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft leads can be updated"
        )
    
    updated_lead = await lead_service.update_lead(
        db,
        lead,
        **lead_data.model_dump(exclude_unset=True)
    )
    
    return updated_lead


@router.post("/{lead_id}/submit", response_model=LeadResponse)
async def submit_lead_for_review(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Submit lead for admin review."""
    
    lead = await lead_service.get_lead_by_id(db, lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only submit your own leads"
        )
    
    try:
        submitted_lead = await lead_service.submit_for_review(db, lead)
        return submitted_lead
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{lead_id}/interest", status_code=status.HTTP_201_CREATED)
async def express_interest(
    lead_id: int,
    interest_data: LeadInterestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_vendor),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Express interest in a lead (vendor only)."""
    
    success, interest, error = await lead_service.express_interest(
        db,
        lead_id=lead_id,
        vendor_id=current_user.id,
        pitch=interest_data.pitch
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"message": "Interest expressed successfully", "interest_id": interest.id}


@router.get("/{lead_id}/interests", response_model=list[LeadInterestResponse])
async def get_lead_interests(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Get all interests for a lead (buyer only)."""
    
    lead = await lead_service.get_lead_by_id(db, lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view interests for your own leads"
        )
    
    interests = await lead_service.get_lead_interests(db, lead_id)
    
    # Enrich with vendor info
    result = []
    for interest in interests:
        # Get vendor info
        from sqlalchemy import select
        stmt = select(User, VendorProfile).join(
            VendorProfile, User.id == VendorProfile.user_id
        ).where(User.id == interest.vendor_id)
        user_result = await db.execute(stmt)
        user_data = user_result.first()
        
        result.append(LeadInterestResponse(
            id=interest.id,
            lead_id=interest.lead_id,
            vendor_id=interest.vendor_id,
            vendor_username=user_data[0].username if user_data else "Unknown",
            vendor_organization=user_data[1].organization if user_data and user_data[1] else None,
            pitch=interest.pitch,
            status=interest.status.value,
            created_at=interest.created_at
        ))
    
    return result


@router.post("/{lead_id}/accept/{vendor_id}")
async def accept_vendor(
    lead_id: int,
    vendor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
    lead_service: LeadService = Depends(get_lead_service)
):
    """Accept a vendor's interest (buyer only)."""
    
    lead = await lead_service.get_lead_by_id(db, lead_id)
    
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only accept vendors for your own leads"
        )
    
    success, conversation, error = await lead_service.accept_vendor(
        db,
        lead,
        vendor_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {
        "message": "Vendor accepted successfully",
        "conversation_id": conversation.id
    }
