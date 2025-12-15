"""Support listing API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user, get_current_source, get_current_buyer
from app.services.listing_service import ListingService
from app.services.monero_service import MoneroService
from app.services.price_oracle import PriceOracle
from app.models.user import User
from app.schemas.listing import (
    ListingCreate,
    ListingUpdate,
    ListingResponse,
    ListingDetailResponse,
    ListingListResponse,
    SupportTierCreate,
    SupportTierResponse,
    ContributionInitiateRequest,
    ContributionInitiateResponse,
    ListingUpdateCreate,
    ListingUpdateResponse,
)

router = APIRouter(prefix="/api/listings", tags=["listings"])


async def get_listing_service() -> ListingService:
    """Dependency for listing service."""
    return ListingService(MoneroService(), PriceOracle())


@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    listing_data: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_buyer),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Create a new support listing (buyer only)."""
    
    success, listing, error = await listing_service.create_listing(
        db,
        buyer_id=current_user.id,
        title=listing_data.title,
        slug=listing_data.slug,
        category=listing_data.category,
        story=listing_data.story,
        goals=listing_data.goals,
        use_of_funds=listing_data.use_of_funds,
        target_amount_usd=listing_data.target_amount_usd
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return listing


@router.get("", response_model=ListingListResponse)
async def list_listings(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    listing_service: ListingService = Depends(get_listing_service)
):
    """List active support listings (public)."""
    
    skip = (page - 1) * page_size
    listings, total = await listing_service.list_active_listings(
        db,
        category=category,
        skip=skip,
        limit=page_size
    )
    
    return ListingListResponse(
        listings=listings,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{slug}", response_model=ListingDetailResponse)
async def get_listing(
    slug: str,
    db: AsyncSession = Depends(get_db),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Get a listing by slug (public)."""
    
    listing = await listing_service.get_listing_by_slug(db, slug)
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    return ListingDetailResponse(
        id=listing.id,
        buyer_id=listing.buyer_id,
        title=listing.title,
        slug=listing.slug,
        category=listing.category.value,
        story=listing.story,
        goals=listing.goals,
        use_of_funds=listing.use_of_funds,
        target_amount_usd=listing.target_amount_usd,
        current_amount_usd=listing.current_amount_usd,
        status=listing.status.value,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
        published_at=listing.published_at,
        tiers=[],
        supporter_count=0
    )


@router.post("/{listing_id}/tiers", response_model=SupportTierResponse, status_code=status.HTTP_201_CREATED)
async def add_tier(
    listing_id: int,
    tier_data: SupportTierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_source),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Add a tier to a listing (source only)."""
    
    listing = await listing_service.get_listing_by_id(db, listing_id)
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    if listing.source_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own listings"
        )
    
    tier = await listing_service.add_tier(
        db,
        listing_id=listing_id,
        name=tier_data.name,
        amount_usd=tier_data.amount_usd,
        description=tier_data.description,
        perks=tier_data.perks,
        max_supporters=tier_data.max_supporters
    )
    
    return tier


@router.post("/{slug}/contribute", response_model=ContributionInitiateResponse)
async def initiate_contribution(
    slug: str,
    contribution_data: ContributionInitiateRequest,
    db: AsyncSession = Depends(get_db),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Initiate a contribution to a listing (public)."""
    
    listing = await listing_service.get_listing_by_slug(db, slug)
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    success, contribution, error = await listing_service.initiate_contribution(
        db,
        listing_id=listing.id,
        tier_id=contribution_data.tier_id,
        custom_amount_usd=contribution_data.custom_amount_usd,
        display_on_wall=contribution_data.display_on_wall,
        supporter_display_name=contribution_data.supporter_display_name,
        supporter_message=contribution_data.supporter_message
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Convert atomic units to XMR for display
    xmr_amount = float(contribution.amount_xmr_atomic) / 1e12
    
    return ContributionInitiateResponse(
        contribution_id=contribution.id,
        monero_address=contribution.monero_address,
        payment_id=contribution.payment_id,
        amount_xmr=f"{xmr_amount:.12f}",
        amount_usd=contribution.amount_usd_at_contribution,
        expires_at=contribution.created_at  # Would add expiry logic
    )


@router.post("/{listing_id}/updates", response_model=ListingUpdateResponse, status_code=status.HTTP_201_CREATED)
async def post_listing_update(
    listing_id: int,
    update_data: ListingUpdateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_source),
    listing_service: ListingService = Depends(get_listing_service)
):
    """Post an update to a listing (source only)."""
    
    listing = await listing_service.get_listing_by_id(db, listing_id)
    
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found"
        )
    
    if listing.source_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own listings"
        )
    
    update = await listing_service.post_update(
        db,
        listing_id=listing_id,
        title=update_data.title,
        content=update_data.content
    )
    
    return update
