"""Admin service for platform moderation and management."""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.user import User, UserRole, VendorProfile, BuyerProfile, VerificationStatus
from app.models.lead import Lead, LeadStatus
from app.models.listing import Listing, ListingStatus
from app.models.system import AuditLog, AuditAction


class AdminService:
    """Service for administrative operations and moderation."""
    
    def __init__(self, db: AsyncSession, admin_user: User):
        self.db = db
        self.admin_user = admin_user
        
        if admin_user.role != UserRole.ADMIN:
            raise PermissionError("User is not an administrator")
    
    async def verify_vendor(
        self,
        vendor_id: int,
        approved: bool,
        notes: Optional[str] = None
    ) -> VendorProfile:
        """
        Verify or reject a vendor account.
        
        Args:
            vendor_id: Vendor user ID
            approved: True to approve, False to reject
            notes: Admin notes for decision
            
        Returns:
            Updated vendor profile
        """
        stmt = select(VendorProfile).where(VendorProfile.user_id == vendor_id)
        result = await self.db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if not profile:
            raise ValueError("Vendor profile not found")
        
        profile.verification_status = (
            VerificationStatus.VERIFIED if approved else VerificationStatus.REJECTED
        )
        
        # Log action
        audit = AuditLog(
            user_id=self.admin_user.id,
            action=AuditAction.VENDOR_VERIFIED if approved else AuditAction.VENDOR_REJECTED,
            details={"vendor_id": vendor_id, "notes": notes}
        )
        self.db.add(audit)
        
        await self.db.commit()
        await self.db.refresh(profile)
        
        return profile
    
    async def moderate_lead(
        self,
        lead_id: int,
        approved: bool,
        rejection_reason: Optional[str] = None
    ) -> Lead:
        """Moderate a lead posting."""
        stmt = select(Lead).where(Lead.id == lead_id)
        result = await self.db.execute(stmt)
        lead = result.scalar_one_or_none()
        
        if not lead:
            raise ValueError("Lead not found")
        
        lead.status = LeadStatus.ACTIVE if approved else LeadStatus.REJECTED
        
        if rejection_reason:
            lead.rejection_reason = rejection_reason
        
        audit = AuditLog(
            user_id=self.admin_user.id,
            action=AuditAction.LEAD_APPROVED if approved else AuditAction.LEAD_REJECTED,
            details={"lead_id": lead_id, "reason": rejection_reason}
        )
        self.db.add(audit)
        
        await self.db.commit()
        await self.db.refresh(lead)
        
        return lead
    
    async def moderate_listing(
        self,
        listing_id: int,
        approved: bool,
        rejection_reason: Optional[str] = None
    ) -> Listing:
        """Moderate a support listing."""
        stmt = select(Listing).where(Listing.id == listing_id)
        result = await self.db.execute(stmt)
        listing = result.scalar_one_or_none()
        
        if not listing:
            raise ValueError("Listing not found")
        
        listing.status = ListingStatus.ACTIVE if approved else ListingStatus.REJECTED
        
        if rejection_reason:
            listing.rejection_reason = rejection_reason
        
        audit = AuditLog(
            user_id=self.admin_user.id,
            action=AuditAction.LISTING_APPROVED if approved else AuditAction.LISTING_REJECTED,
            details={"listing_id": listing_id, "reason": rejection_reason}
        )
        self.db.add(audit)
        
        await self.db.commit()
        await self.db.refresh(listing)
        
        return listing
    
    async def suspend_user(
        self,
        user_id: int,
        reason: str,
        duration_hours: Optional[int] = None
    ) -> User:
        """Suspend a user account."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        user.is_suspended = True
        user.suspension_reason = reason
        
        if duration_hours:
            from datetime import timedelta
            user.suspended_until = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        audit = AuditLog(
            user_id=self.admin_user.id,
            action=AuditAction.USER_SUSPENDED,
            details={
                "target_user_id": user_id,
                "reason": reason,
                "duration_hours": duration_hours
            }
        )
        self.db.add(audit)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def get_platform_stats(self) -> dict:
        """Get comprehensive platform statistics."""
        # User counts
        total_users = await self.db.scalar(select(func.count(User.id)))
        vendors = await self.db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.VENDOR)
        )
        buyers = await self.db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.BUYER)
        )
        
        # Lead counts
        total_leads = await self.db.scalar(select(func.count(Lead.id)))
        active_leads = await self.db.scalar(
            select(func.count(Lead.id)).where(Lead.status == LeadStatus.ACTIVE)
        )
        
        # Listing counts
        total_listings = await self.db.scalar(select(func.count(Listing.id)))
        active_listings = await self.db.scalar(
            select(func.count(Listing.id)).where(Listing.status == ListingStatus.ACTIVE)
        )
        
        return {
            "users": {
                "total": total_users,
                "vendors": vendors,
                "buyers": buyers,
            },
            "leads": {
                "total": total_leads,
                "active": active_leads,
            },
            "listings": {
                "total": total_listings,
                "active": active_listings,
            }
        }
