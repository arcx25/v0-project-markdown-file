"""Lead management service for vendor-buyer matching."""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from datetime import datetime, timezone

from app.models.lead import Lead, LeadInterest, LeadStatus, LeadCategory, LeadScope, InterestStatus
from app.models.user import User, UserRole, VendorProfile
from app.models.message import Conversation


class LeadService:
    """Service for managing leads and vendor-buyer matching."""
    
    async def create_lead(
        self,
        db: AsyncSession,
        buyer_id: int,
        title: str,
        category: str,
        scope: str,
        summary: str,
        evidence_types: List[str],
        preferred_vendor_qualities: Optional[str] = None
    ) -> Lead:
        """Create a new lead."""
        
        lead = Lead(
            buyer_id=buyer_id,
            title=title,
            category=LeadCategory(category),
            scope=LeadScope(scope),
            summary=summary,
            evidence_types=evidence_types,
            preferred_vendor_qualities=preferred_vendor_qualities,
            status=LeadStatus.DRAFT
        )
        
        db.add(lead)
        await db.commit()
        await db.refresh(lead)
        
        return lead
    
    async def update_lead(
        self,
        db: AsyncSession,
        lead: Lead,
        **kwargs
    ) -> Lead:
        """Update a lead."""
        
        for key, value in kwargs.items():
            if value is not None and hasattr(lead, key):
                if key == 'category':
                    value = LeadCategory(value)
                elif key == 'scope':
                    value = LeadScope(value)
                setattr(lead, key, value)
        
        lead.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(lead)
        
        return lead
    
    async def submit_for_review(
        self,
        db: AsyncSession,
        lead: Lead
    ) -> Lead:
        """Submit lead for admin review."""
        
        if lead.status != LeadStatus.DRAFT:
            raise ValueError("Only draft leads can be submitted for review")
        
        lead.status = LeadStatus.PENDING_REVIEW
        lead.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(lead)
        
        return lead
    
    async def approve_lead(
        self,
        db: AsyncSession,
        lead: Lead,
        admin_id: int
    ) -> Lead:
        """Approve a lead (admin action)."""
        
        if lead.status != LeadStatus.PENDING_REVIEW:
            raise ValueError("Only pending leads can be approved")
        
        lead.status = LeadStatus.ACTIVE
        lead.reviewed_by_id = admin_id
        lead.reviewed_at = datetime.now(timezone.utc)
        lead.published_at = datetime.now(timezone.utc)
        lead.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(lead)
        
        return lead
    
    async def reject_lead(
        self,
        db: AsyncSession,
        lead: Lead,
        admin_id: int,
        reason: str
    ) -> Lead:
        """Reject a lead (admin action)."""
        
        if lead.status != LeadStatus.PENDING_REVIEW:
            raise ValueError("Only pending leads can be rejected")
        
        lead.status = LeadStatus.REJECTED
        lead.reviewed_by_id = admin_id
        lead.reviewed_at = datetime.now(timezone.utc)
        lead.rejection_reason = reason
        lead.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(lead)
        
        return lead
    
    async def get_lead_by_id(
        self,
        db: AsyncSession,
        lead_id: int
    ) -> Optional[Lead]:
        """Get a lead by ID."""
        
        stmt = select(Lead).where(Lead.id == lead_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_active_leads(
        self,
        db: AsyncSession,
        category: Optional[str] = None,
        scope: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Lead], int]:
        """List active leads for vendors to browse."""
        
        # Base query for active leads
        conditions = [Lead.status == LeadStatus.ACTIVE]
        
        if category:
            conditions.append(Lead.category == LeadCategory(category))
        
        if scope:
            conditions.append(Lead.scope == LeadScope(scope))
        
        # Count total
        count_stmt = select(func.count(Lead.id)).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Get leads
        stmt = (
            select(Lead)
            .where(and_(*conditions))
            .order_by(Lead.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        leads = result.scalars().all()
        
        return list(leads), total
    
    async def list_source_leads(
        self,
        db: AsyncSession,
        source_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Lead], int]:
        """List leads created by a specific source."""
        
        # Count total
        count_stmt = select(func.count(Lead.id)).where(Lead.source_id == source_id)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Get leads
        stmt = (
            select(Lead)
            .where(Lead.source_id == source_id)
            .order_by(Lead.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        leads = result.scalars().all()
        
        return list(leads), total
    
    async def list_buyer_leads(
        self,
        db: AsyncSession,
        buyer_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Lead], int]:
        """List leads created by a specific buyer."""
        
        # Count total
        count_stmt = select(func.count(Lead.id)).where(Lead.buyer_id == buyer_id)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Get leads
        stmt = (
            select(Lead)
            .where(Lead.buyer_id == buyer_id)
            .order_by(Lead.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        leads = result.scalars().all()
        
        return list(leads), total
    
    async def express_interest(
        self,
        db: AsyncSession,
        lead_id: int,
        vendor_id: int,
        pitch: str
    ) -> Tuple[bool, Optional[LeadInterest], Optional[str]]:
        """Vendor expresses interest in a lead."""
        
        # Check if lead exists and is active
        lead = await self.get_lead_by_id(db, lead_id)
        if not lead:
            return False, None, "Lead not found"
        
        if lead.status != LeadStatus.ACTIVE:
            return False, None, "Lead is not active"
        
        # Check if already expressed interest
        stmt = select(LeadInterest).where(
            and_(
                LeadInterest.lead_id == lead_id,
                LeadInterest.vendor_id == vendor_id
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            return False, None, "You have already expressed interest in this lead"
        
        # Create interest
        interest = LeadInterest(
            lead_id=lead_id,
            vendor_id=vendor_id,
            pitch=pitch,
            status=InterestStatus.PENDING
        )
        
        db.add(interest)
        await db.commit()
        await db.refresh(interest)
        
        return True, interest, None
    
    async def get_lead_interests(
        self,
        db: AsyncSession,
        lead_id: int
    ) -> List[LeadInterest]:
        """Get all interests for a lead."""
        
        stmt = (
            select(LeadInterest)
            .where(LeadInterest.lead_id == lead_id)
            .order_by(LeadInterest.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    async def accept_vendor(
        self,
        db: AsyncSession,
        lead: Lead,
        vendor_id: int
    ) -> Tuple[bool, Optional[Conversation], Optional[str]]:
        """Buyer accepts a vendor and creates a conversation."""
        
        if lead.status != LeadStatus.ACTIVE:
            return False, None, "Lead is not active"
        
        # Get the interest
        stmt = select(LeadInterest).where(
            and_(
                LeadInterest.lead_id == lead.id,
                LeadInterest.vendor_id == vendor_id,
                LeadInterest.status == InterestStatus.PENDING
            )
        )
        result = await db.execute(stmt)
        interest = result.scalar_one_or_none()
        
        if not interest:
            return False, None, "Interest not found or already processed"
        
        # Update interest status
        interest.status = InterestStatus.ACCEPTED
        interest.responded_at = datetime.now(timezone.utc)
        
        # Update lead
        lead.status = LeadStatus.MATCHED
        lead.matched_vendor_id = vendor_id
        lead.updated_at = datetime.now(timezone.utc)
        
        # Decline other pending interests
        stmt = select(LeadInterest).where(
            and_(
                LeadInterest.lead_id == lead.id,
                LeadInterest.id != interest.id,
                LeadInterest.status == InterestStatus.PENDING
            )
        )
        result = await db.execute(stmt)
        other_interests = result.scalars().all()
        
        for other in other_interests:
            other.status = InterestStatus.DECLINED
            other.responded_at = datetime.now(timezone.utc)
        
        # Create conversation
        conversation = Conversation(
            lead_id=lead.id,
            buyer_id=lead.buyer_id,
            vendor_id=vendor_id,
            last_message_at=datetime.now(timezone.utc)
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        return True, conversation, None
