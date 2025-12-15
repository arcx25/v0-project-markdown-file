"""Support listing service."""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.listing import (
    SupportListing,
    SupportTier,
    SupportContribution,
    SupporterWallEntry,
    ListingUpdate,
    ListingStatus,
    ListingCategory
)
from app.services.monero_service import MoneroService
from app.services.price_oracle import PriceOracle


class ListingService:
    """Service for managing support listings."""
    
    def __init__(self, monero_service: MoneroService, price_oracle: PriceOracle):
        self.monero = monero_service
        self.price_oracle = price_oracle
    
    async def create_listing(
        self,
        db: AsyncSession,
        source_id: int,
        title: str,
        slug: str,
        category: str,
        story: str,
        goals: str,
        use_of_funds: Optional[str] = None,
        target_amount_usd: Optional[int] = None
    ) -> Tuple[bool, Optional[SupportListing], Optional[str]]:
        """Create a new support listing."""
        
        # Check if slug is unique
        stmt = select(SupportListing).where(SupportListing.slug == slug)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            return False, None, "Slug already taken"
        
        listing = SupportListing(
            source_id=source_id,
            title=title,
            slug=slug,
            category=ListingCategory(category),
            story=story,
            goals=goals,
            use_of_funds=use_of_funds,
            target_amount_usd=target_amount_usd,
            status=ListingStatus.DRAFT
        )
        
        db.add(listing)
        await db.commit()
        await db.refresh(listing)
        
        return True, listing, None
    
    async def get_listing_by_id(
        self,
        db: AsyncSession,
        listing_id: int
    ) -> Optional[SupportListing]:
        """Get a listing by ID."""
        
        stmt = select(SupportListing).where(SupportListing.id == listing_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_listing_by_slug(
        self,
        db: AsyncSession,
        slug: str
    ) -> Optional[SupportListing]:
        """Get a listing by slug."""
        
        stmt = select(SupportListing).where(SupportListing.slug == slug)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_active_listings(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[SupportListing], int]:
        """List active support listings."""
        
        conditions = [SupportListing.status == ListingStatus.ACTIVE]
        
        if category:
            conditions.append(SupportListing.category == ListingCategory(category))
        
        # Count total
        count_stmt = select(func.count(SupportListing.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Get listings
        stmt = (
            select(SupportListing)
            .where(and_(*conditions))
            .order_by(SupportListing.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        listings = result.scalars().all()
        
        return list(listings), total
    
    async def add_tier(
        self,
        db: AsyncSession,
        listing_id: int,
        name: str,
        amount_usd: int,
        description: Optional[str],
        perks: List[str],
        max_supporters: Optional[int]
    ) -> SupportTier:
        """Add a tier to a listing."""
        
        # Get max display order
        stmt = select(func.max(SupportTier.display_order)).where(
            SupportTier.listing_id == listing_id
        )
        result = await db.execute(stmt)
        max_order = result.scalar() or 0
        
        tier = SupportTier(
            listing_id=listing_id,
            name=name,
            amount_usd=amount_usd,
            description=description,
            perks=perks,
            max_supporters=max_supporters,
            display_order=max_order + 1
        )
        
        db.add(tier)
        await db.commit()
        await db.refresh(tier)
        
        return tier
    
    async def initiate_contribution(
        self,
        db: AsyncSession,
        listing_id: int,
        tier_id: Optional[int],
        custom_amount_usd: Optional[int],
        display_on_wall: bool,
        supporter_display_name: Optional[str],
        supporter_message: Optional[str]
    ) -> Tuple[bool, Optional[SupportContribution], Optional[str]]:
        """Initiate a contribution to a listing."""
        
        # Get listing
        listing = await self.get_listing_by_id(db, listing_id)
        if not listing or listing.status != ListingStatus.ACTIVE:
            return False, None, "Listing not available"
        
        # Determine amount
        amount_usd = 0
        if tier_id:
            stmt = select(SupportTier).where(SupportTier.id == tier_id)
            result = await db.execute(stmt)
            tier = result.scalar_one_or_none()
            
            if not tier or tier.listing_id != listing_id:
                return False, None, "Invalid tier"
            
            # Check if tier is full
            if tier.max_supporters and tier.current_supporters >= tier.max_supporters:
                return False, None, "Tier is full"
            
            amount_usd = tier.amount_usd
        elif custom_amount_usd:
            amount_usd = custom_amount_usd
        else:
            return False, None, "Must specify tier or custom amount"
        
        # Get current XMR price
        xmr_price = await self.price_oracle.get_xmr_price_usd()
        
        # Convert to XMR atomic units
        amount_xmr_atomic = self.price_oracle.usd_to_xmr(amount_usd * 100, xmr_price)  # USD to cents
        
        # Generate integrated address
        address, payment_id = await self.monero.generate_integrated_address()
        
        # Create contribution record
        contribution = SupportContribution(
            listing_id=listing_id,
            tier_id=tier_id,
            amount_xmr_atomic=amount_xmr_atomic,
            amount_usd_at_contribution=amount_usd,
            monero_address=address,
            payment_id=payment_id,
            display_on_wall=display_on_wall,
            supporter_display_name=supporter_display_name,
            supporter_message=supporter_message,
            confirmed=False
        )
        
        db.add(contribution)
        await db.commit()
        await db.refresh(contribution)
        
        return True, contribution, None
    
    async def post_update(
        self,
        db: AsyncSession,
        listing_id: int,
        title: str,
        content: str
    ) -> ListingUpdate:
        """Post an update to a listing."""
        
        update = ListingUpdate(
            listing_id=listing_id,
            title=title,
            content=content
        )
        
        db.add(update)
        await db.commit()
        await db.refresh(update)
        
        return update
