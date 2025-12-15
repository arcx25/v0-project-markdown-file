"""Payment monitoring worker."""

from celery import shared_task
from sqlalchemy import select, and_
from datetime import datetime, timezone

from app.workers.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models.payment import Deposit, DepositStatus, SupportContribution
from app.models.listing import SupportListing, SupportTier, SupporterWallEntry
from app.services.monero_service import MoneroService
from app.config import get_settings


@celery_app.task(name="app.workers.payment_monitor.monitor_pending_payments")
def monitor_pending_payments():
    """Monitor pending payments and update status."""
    import asyncio
    asyncio.run(_monitor_pending_payments())


async def _monitor_pending_payments():
    """Async implementation of payment monitoring."""
    
    settings = get_settings()
    monero = MoneroService()
    
    async with AsyncSessionLocal() as db:
        # Get all unconfirmed contributions
        stmt = select(SupportContribution).where(
            and_(
                SupportContribution.confirmed == False,
                SupportContribution.created_at > datetime.now(timezone.utc)  # Not expired
            )
        )
        result = await db.execute(stmt)
        contributions = result.scalars().all()
        
        for contribution in contributions:
            try:
                # Check payment status
                received, amount, confirmations = await monero.check_payment(
                    contribution.payment_id,
                    int(contribution.amount_xmr_atomic)
                )
                
                if received:
                    # Update confirmations
                    contribution.confirmations = confirmations
                    
                    # If enough confirmations, mark as confirmed
                    if confirmations >= settings.MONERO_CONFIRMATIONS_REQUIRED:
                        contribution.confirmed = True
                        contribution.confirmed_at = datetime.now(timezone.utc)
                        
                        # Update listing total
                        stmt = select(SupportListing).where(
                            SupportListing.id == contribution.listing_id
                        )
                        result = await db.execute(stmt)
                        listing = result.scalar_one_or_none()
                        
                        if listing:
                            listing.current_amount_usd += contribution.amount_usd_at_contribution
                        
                        # Update tier supporter count if applicable
                        if contribution.tier_id:
                            stmt = select(SupportTier).where(
                                SupportTier.id == contribution.tier_id
                            )
                            result = await db.execute(stmt)
                            tier = result.scalar_one_or_none()
                            
                            if tier:
                                tier.current_supporters += 1
                        
                        # Add to supporter wall if requested
                        if contribution.display_on_wall:
                            display_name = contribution.supporter_display_name or "Anonymous Supporter"
                            
                            # Determine amount range for display
                            amount_range = f"${contribution.amount_usd_at_contribution}"
                            if contribution.amount_usd_at_contribution >= 1000:
                                amount_range = "$1000+"
                            elif contribution.amount_usd_at_contribution >= 500:
                                amount_range = "$500-$999"
                            elif contribution.amount_usd_at_contribution >= 100:
                                amount_range = "$100-$499"
                            elif contribution.amount_usd_at_contribution >= 50:
                                amount_range = "$50-$99"
                            else:
                                amount_range = "$1-$49"
                            
                            # Get tier name if applicable
                            tier_name = None
                            if contribution.tier_id:
                                stmt = select(SupportTier).where(
                                    SupportTier.id == contribution.tier_id
                                )
                                result = await db.execute(stmt)
                                tier = result.scalar_one_or_none()
                                if tier:
                                    tier_name = tier.name
                            
                            wall_entry = SupporterWallEntry(
                                listing_id=contribution.listing_id,
                                contribution_id=contribution.id,
                                display_name=display_name,
                                tier_name=tier_name,
                                amount_display=amount_range,
                                message=contribution.supporter_message
                            )
                            
                            db.add(wall_entry)
                        
                        print(f"[v0] Contribution {contribution.id} confirmed with {confirmations} confirmations")
                
            except Exception as e:
                print(f"[v0] Error monitoring contribution {contribution.id}: {e}")
                continue
        
        await db.commit()
