"""
Comprehensive subscription management service for vendor tiers.
Handles payment processing, tier upgrades, renewals, and grace periods.
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Dict, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.user import User, VendorProfile
from app.models.payment import (
    Subscription,
    SubscriptionTier,
    SubscriptionStatus,
    Deposit,
    DepositStatus,
    DepositPurpose
)
from app.services.pgp_service import pgp_service
from app.services.monero_service import MoneroService
from app.services.price_oracle import PriceOracle
from app.config import settings

logger = logging.getLogger(__name__)

SUBSCRIPTION_PLANS = {
    SubscriptionTier.FREE: {
        "name": "Free Vendor",
        "price_usd_cents": 0,
        "features": [
            "Browse opportunities",
            "Submit proposals (5/month)",
            "Basic messaging",
            "Profile listing"
        ],
        "limits": {
            "proposals_per_month": 5,
            "active_conversations": 3,
            "listing_images": 1
        },
    },
    SubscriptionTier.FREELANCER: {
        "name": "Professional Vendor",
        "price_usd_cents": settings.PRICE_FREELANCER_MONTHLY,
        "features": [
            "Unlimited proposals",
            "Unlimited conversations",
            "Priority in buyer matching",
            "Verified vendor badge",
            "Early access to opportunities",
            "5 listing images"
        ],
        "limits": {
            "proposals_per_month": -1,
            "active_conversations": -1,
            "listing_images": 5
        },
    },
    SubscriptionTier.OUTLET: {
        "name": "Premium Vendor",
        "price_usd_cents": settings.PRICE_OUTLET_MONTHLY,
        "features": [
            "Everything in Professional",
            "Team accounts (up to 5)",
            "API access",
            "Featured listing placement",
            "Dedicated support",
            "Custom storefronts",
            "20 listing images"
        ],
        "limits": {
            "proposals_per_month": -1,
            "active_conversations": -1,
            "team_members": 5,
            "listing_images": 20
        },
    },
    SubscriptionTier.ENTERPRISE: {
        "name": "Enterprise Vendor",
        "price_usd_cents": settings.PRICE_ENTERPRISE_MONTHLY,
        "features": [
            "Everything in Premium",
            "Unlimited team members",
            "White-label marketplace",
            "Custom integrations",
            "SLA guarantees",
            "Multi-vendor management",
            "Unlimited listing images"
        ],
        "limits": {
            "proposals_per_month": -1,
            "active_conversations": -1,
            "team_members": -1,
            "listing_images": -1
        },
    },
}


class SubscriptionService:
    """Comprehensive subscription lifecycle management."""
    
    def __init__(self):
        self.monero = MoneroService()
        self.price_oracle = PriceOracle()
    
    async def get_subscription_plans(self) -> List[Dict]:
        """Get available subscription plans with current XMR pricing."""
        try:
            xmr_price = await self.price_oracle.get_xmr_usd_price()
        except Exception:
            xmr_price = None
        
        plans = []
        for tier, details in SUBSCRIPTION_PLANS.items():
            plan = {
                "tier": tier.value,
                "name": details["name"],
                "price_usd_cents": details["price_usd_cents"],
                "price_usd_display": f"${details['price_usd_cents'] / 100:.2f}/mo",
                "features": details["features"],
                "limits": details["limits"],
            }
            
            if xmr_price and details["price_usd_cents"] > 0:
                price_xmr = Decimal(details["price_usd_cents"]) / 100 / xmr_price
                plan["price_xmr"] = f"{price_xmr:.6f}"
                plan["price_xmr_display"] = f"{price_xmr:.4f} XMR/mo"
            
            plans.append(plan)
        
        return plans
    
    async def get_current_subscription(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Optional[Dict]:
        """Get user's current subscription status."""
        # Get vendor profile
        result = await db.execute(
            select(VendorProfile).where(VendorProfile.id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return None
        
        # Get active subscription
        result = await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.EXPIRING,
                SubscriptionStatus.GRACE_PERIOD,
            ]))
            .order_by(Subscription.expires_at.desc())
        )
        subscription = result.scalar_one_or_none()
        
        tier = SubscriptionTier(profile.subscription_tier)
        plan_details = SUBSCRIPTION_PLANS.get(tier, SUBSCRIPTION_PLANS[SubscriptionTier.FREE])
        
        response = {
            "tier": tier.value,
            "tier_name": plan_details["name"],
            "features": plan_details["features"],
            "limits": plan_details["limits"],
            "is_active": profile.is_subscribed,
        }
        
        if subscription:
            response.update({
                "subscription_id": str(subscription.id),
                "status": subscription.status.value,
                "started_at": subscription.started_at.isoformat(),
                "expires_at": subscription.expires_at.isoformat(),
                "auto_renew": subscription.auto_renew,
                "payment_method": subscription.payment_method,
                "days_remaining": max(0, (subscription.expires_at - datetime.now(timezone.utc)).days),
            })
        
        return response
    
    async def create_subscription(
        self,
        db: AsyncSession,
        user_id: UUID,
        tier: SubscriptionTier,
        payment_method: str = "xmr"
    ) -> Dict:
        """Create or upgrade subscription with XMR payment."""
        if tier == SubscriptionTier.FREE:
            raise ValueError("Cannot subscribe to free tier")
        
        plan = SUBSCRIPTION_PLANS[tier]
        price_cents = plan["price_usd_cents"]
        
        # Check for existing active subscription
        result = await db.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
        )
        existing = result.scalar_one_or_none()
        
        if existing and existing.tier == tier:
            raise ValueError("Already subscribed to this tier")
        
        # Get XMR price
        xmr_price = await self.price_oracle.get_xmr_usd_price()
        price_usd = Decimal(price_cents) / 100
        price_xmr = price_usd / xmr_price
        amount_atomic = self.monero.xmr_to_atomic(price_xmr)
        
        # Create deposit address
        deposit = await self.monero.create_deposit_address(
            db=db,
            user_id=str(user_id),
            purpose=DepositPurpose.SUBSCRIPTION,
            expected_amount_atomic=amount_atomic,
            reference_id=f"subscription:{tier.value}",
            expires_hours=24,
        )
        
        # Create pending subscription
        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            price_usd_cents=price_cents,
            price_xmr_atomic=amount_atomic,
            started_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            status=SubscriptionStatus.PENDING,
            payment_method="xmr",
            payment_reference=str(deposit.id),
        )
        db.add(subscription)
        await db.commit()
        
        return {
            "subscription_id": str(subscription.id),
            "tier": tier.value,
            "amount_usd": f"${price_usd:.2f}",
            "amount_xmr": f"{price_xmr:.12f}",
            "xmr_address": deposit.address,
            "payment_id": deposit.payment_id,
            "qr_code_base64": deposit.qr_code_base64,
            "expires_at": deposit.expires_at.isoformat(),
            "exchange_rate": f"1 XMR = ${xmr_price:.2f} USD",
        }
    
    async def process_subscription_payment(
        self,
        db: AsyncSession,
        deposit: Deposit
    ) -> bool:
        """Activate subscription when payment is confirmed."""
        if not deposit.reference_id or not deposit.reference_id.startswith("subscription:"):
            return False
        
        tier_value = deposit.reference_id.split(":")[1]
        tier = SubscriptionTier(tier_value)
        
        # Find pending subscription
        result = await db.execute(
            select(Subscription)
            .where(Subscription.payment_reference == str(deposit.id))
            .where(Subscription.status == SubscriptionStatus.PENDING)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return False
        
        # Activate subscription
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.started_at = datetime.now(timezone.utc)
        subscription.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Update vendor profile
        result = await db.execute(
            select(VendorProfile).where(VendorProfile.id == subscription.user_id)
        )
        profile = result.scalar_one_or_none()
        
        if profile:
            profile.subscription_tier = tier.value
            profile.subscription_expires_at = subscription.expires_at
        
        await db.commit()
        logger.info(f"Activated subscription for user {subscription.user_id}, tier {tier.value}")
        
        return True
    
    async def check_expiring_subscriptions(self, db: AsyncSession) -> int:
        """Check and handle expiring subscriptions with grace periods."""
        now = datetime.now(timezone.utc)
        processed = 0
        
        # Find subscriptions expiring in next 7 days
        result = await db.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(Subscription.expires_at <= now + timedelta(days=7))
            .where(Subscription.expires_at > now)
        )
        expiring_soon = result.scalars().all()
        
        for subscription in expiring_soon:
            if not subscription.auto_renew:
                subscription.status = SubscriptionStatus.EXPIRING
                processed += 1
        
        # Handle expired subscriptions - enter grace period
        result = await db.execute(
            select(Subscription)
            .where(Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.EXPIRING,
            ]))
            .where(Subscription.expires_at <= now)
        )
        expired = result.scalars().all()
        
        for subscription in expired:
            if subscription.status != SubscriptionStatus.GRACE_PERIOD:
                subscription.status = SubscriptionStatus.GRACE_PERIOD
                subscription.expires_at = now + timedelta(days=3)
                processed += 1
        
        # Handle grace period expiration - downgrade to free
        result = await db.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.GRACE_PERIOD)
            .where(Subscription.expires_at <= now)
        )
        grace_expired = result.scalars().all()
        
        for subscription in grace_expired:
            subscription.status = SubscriptionStatus.EXPIRED
            
            # Downgrade profile to free
            result = await db.execute(
                select(VendorProfile).where(VendorProfile.id == subscription.user_id)
            )
            profile = result.scalar_one_or_none()
            
            if profile:
                profile.subscription_tier = SubscriptionTier.FREE.value
                profile.subscription_expires_at = None
            
            processed += 1
        
        await db.commit()
        return processed
    
    async def cancel_subscription(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        user_id: UUID
    ) -> bool:
        """Cancel subscription auto-renewal."""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription_id)
            .where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return False
        
        subscription.auto_renew = False
        subscription.status = SubscriptionStatus.EXPIRING
        await db.commit()
        
        logger.info(f"Cancelled subscription {subscription_id} for user {user_id}")
        return True


subscription_service = SubscriptionService()
