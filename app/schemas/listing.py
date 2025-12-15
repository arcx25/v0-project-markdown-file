"""Support listing schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class SupportTierCreate(BaseModel):
    """Create a support tier."""
    name: str = Field(..., min_length=3, max_length=100)
    amount_usd: int = Field(..., ge=1)
    description: Optional[str] = Field(None, max_length=500)
    perks: List[str] = Field(default_factory=list)
    max_supporters: Optional[int] = Field(None, ge=1)


class SupportTierResponse(BaseModel):
    """Support tier response."""
    id: int
    name: str
    amount_usd: int
    description: Optional[str]
    perks: Optional[List[str]]
    max_supporters: Optional[int]
    current_supporters: int
    display_order: int
    
    class Config:
        from_attributes = True


class ListingCreate(BaseModel):
    """Create a support listing."""
    title: str = Field(..., min_length=10, max_length=500)
    slug: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-z0-9-]+$")
    category: str
    story: str = Field(..., min_length=100, max_length=10000)
    goals: str = Field(..., min_length=50, max_length=5000)
    use_of_funds: Optional[str] = Field(None, max_length=5000)
    target_amount_usd: Optional[int] = Field(None, ge=1)


class ListingUpdate(BaseModel):
    """Update a support listing."""
    title: Optional[str] = Field(None, min_length=10, max_length=500)
    story: Optional[str] = Field(None, min_length=100, max_length=10000)
    goals: Optional[str] = Field(None, min_length=50, max_length=5000)
    use_of_funds: Optional[str] = Field(None, max_length=5000)
    target_amount_usd: Optional[int] = Field(None, ge=1)


class ListingResponse(BaseModel):
    """Support listing response."""
    id: int
    buyer_id: int
    title: str
    slug: str
    category: str
    story: str
    goals: str
    use_of_funds: Optional[str]
    target_amount_usd: Optional[int]
    current_amount_usd: int
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ListingDetailResponse(ListingResponse):
    """Detailed listing with tiers and supporters."""
    tiers: List[SupportTierResponse]
    supporter_count: int


class ListingListResponse(BaseModel):
    """List of support listings."""
    listings: List[ListingResponse]
    total: int
    page: int
    page_size: int


class ContributionInitiateRequest(BaseModel):
    """Initiate a contribution."""
    tier_id: Optional[int] = None
    custom_amount_usd: Optional[int] = Field(None, ge=1)
    display_on_wall: bool = True
    supporter_display_name: Optional[str] = Field(None, max_length=100)
    supporter_message: Optional[str] = Field(None, max_length=500)


class ContributionInitiateResponse(BaseModel):
    """Response with payment details."""
    contribution_id: int
    monero_address: str
    payment_id: str
    amount_xmr: str
    amount_usd: int
    expires_at: datetime


class ListingUpdateCreate(BaseModel):
    """Create a listing update."""
    title: str = Field(..., min_length=5, max_length=500)
    content: str = Field(..., min_length=50, max_length=10000)


class ListingUpdateResponse(BaseModel):
    """Listing update response."""
    id: int
    listing_id: int
    title: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True
