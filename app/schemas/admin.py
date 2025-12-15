"""Admin schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PendingLeadResponse(BaseModel):
    """Pending lead for review."""
    id: int
    buyer_id: int
    buyer_username: str
    title: str
    category: str
    scope: str
    summary: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApproveLeadRequest(BaseModel):
    """Approve a lead."""
    pass


class RejectLeadRequest(BaseModel):
    """Reject a lead."""
    reason: str = Field(..., min_length=10, max_length=1000)


class PendingVendorResponse(BaseModel):
    """Pending vendor verification."""
    id: int
    user_id: int
    username: str
    organization: Optional[str]
    position: Optional[str]
    website: Optional[str]
    bio: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VerifyVendorRequest(BaseModel):
    """Verify a vendor."""
    notes: Optional[str] = Field(None, max_length=1000)


class PendingListingResponse(BaseModel):
    """Pending listing for review."""
    id: int
    buyer_id: int
    buyer_username: str
    title: str
    slug: str
    category: str
    story: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserManagementResponse(BaseModel):
    """User for admin management."""
    id: int
    username: str
    role: str
    is_active: bool
    is_suspended: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SuspendUserRequest(BaseModel):
    """Suspend a user."""
    reason: str = Field(..., min_length=10, max_length=1000)
