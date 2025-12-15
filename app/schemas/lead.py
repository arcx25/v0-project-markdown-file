"""Lead schemas."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LeadCreate(BaseModel):
    """Create a new lead."""
    title: str = Field(..., min_length=10, max_length=500)
    category: str
    scope: str
    summary: str = Field(..., min_length=50, max_length=5000)
    evidence_types: List[str] = Field(default_factory=list)
    preferred_journalist_qualities: Optional[str] = Field(None, max_length=2000)


class LeadUpdate(BaseModel):
    """Update an existing lead."""
    title: Optional[str] = Field(None, min_length=10, max_length=500)
    category: Optional[str] = None
    scope: Optional[str] = None
    summary: Optional[str] = Field(None, min_length=50, max_length=5000)
    evidence_types: Optional[List[str]] = None
    preferred_journalist_qualities: Optional[str] = Field(None, max_length=2000)


class LeadResponse(BaseModel):
    """Lead response."""
    id: int
    source_id: int
    title: str
    category: str
    scope: str
    summary: str
    evidence_types: Optional[List[str]]
    preferred_journalist_qualities: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """List of leads for browsing."""
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int


class LeadInterestCreate(BaseModel):
    """Express interest in a lead."""
    pitch: str = Field(..., min_length=100, max_length=2000)


class LeadInterestResponse(BaseModel):
    """Lead interest response."""
    id: int
    lead_id: int
    journalist_id: int
    journalist_username: str
    journalist_organization: Optional[str]
    pitch: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AcceptJournalistRequest(BaseModel):
    """Accept a journalist's interest."""
    journalist_id: int
