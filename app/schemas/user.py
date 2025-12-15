"""User schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user information."""
    username: str
    role: str


class UserProfile(UserBase):
    """User profile with extended information."""
    id: int
    created_at: datetime
    is_active: bool
    
    organization: Optional[str] = None
    position: Optional[str] = None
    website: Optional[str] = None
    bio: Optional[str] = None
    verification_status: Optional[str] = None
    subscription_tier: Optional[str] = None
    
    anonymous_alias: Optional[str] = None
    trust_score: Optional[int] = None
    
    class Config:
        from_attributes = True
