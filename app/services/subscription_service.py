"""
Business logic for subscription management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from app.models.payment import Subscription, SubscriptionTier, Deposit
from app.models.user import User
from app.services.monero_service import MoneroService
from app.services.price_oracle import PriceOracle

logger = logging.getLogger(__name__)

TIER_PRICES = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.FREELANCER: 50,
    SubscriptionTier.OUTLET: 500,
    SubscriptionTier.ENTERPRISE: 2000
}


async def get_active_subscription(
    db: AsyncSession,
    user_id: int
) -> Optional[Subscription]:
    """Get user's active subscription"""
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status == "ACTIVE",
            Subscription.expires_at > datetime.utcnow()
        )
        .order_by(Subscription.started_at.desc())
    )
    return result.scalar_one_or_none()


async def create_subscription(
    db: AsyncSession,
    user_id: int,
    tier: SubscriptionTier,
    payment_method: str
) -> dict:
    """
    Create new subscription
    Returns payment instructions
    """
    price_usd = TIER_PRICES[tier]
    
    if payment_method == "MONERO":
        # Generate XMR payment address
        monero = MoneroService()
        price_oracle = PriceOracle()
        
        xmr_rate = await price_oracle.get_xmr_rate()
        amount_xmr = price_usd / xmr_rate
        
        # Generate integrated address
        payment_info = await monero.create_integrated_address(
            label=f"subscription_{user_id}_{tier}"
        )
        
        # Create pending deposit
        deposit = Deposit(
            user_id=user_id,
            address=payment_info["address"],
            payment_id=payment_info["payment_id"],
            expected_amount_xmr_atomic=int(amount_xmr * 1e12),
            status="PENDING",
            type="SUBSCRIPTION",
            metadata={"tier": tier}
        )
        db.add(deposit)
        await db.commit()
        
        return {
            "payment_method": "MONERO",
            "amount_usd": price_usd,
            "amount_xmr": amount_xmr,
            "address": payment_info["address"],
            "payment_id": payment_info["payment_id"],
            "instructions": "Send exactly the specified XMR amount to the address provided. Subscription activates after 10 confirmations."
        }
    
    elif payment_method == "STRIPE":
        # TODO: Implement Stripe checkout
        return {
            "payment_method": "STRIPE",
            "checkout_url": "https://stripe.com/checkout/...",
            "instructions": "Complete payment through Stripe"
        }
    
    else:
        raise ValueError(f"Unsupported payment method: {payment_method}")


async def upgrade_subscription(
    db: AsyncSession,
    user_id: int,
    new_tier: SubscriptionTier
) -> dict:
    """Upgrade to higher tier (prorated)"""
    current_sub = await get_active_subscription(db, user_id)
    if not current_sub:
        raise ValueError("No active subscription found")
    
    current_price = TIER_PRICES[current_sub.tier]
    new_price = TIER_PRICES[new_tier]
    
    if new_price <= current_price:
        raise ValueError("Can only upgrade to higher tier")
    
    # Calculate prorated amount
    days_remaining = (current_sub.expires_at - datetime.utcnow()).days
    days_total = 30
    credit = (current_price / days_total) * days_remaining
    amount_due = new_price - credit
    
    # Generate payment for difference
    # (Implementation similar to create_subscription)
    
    return {
        "current_tier": current_sub.tier,
        "new_tier": new_tier,
        "credit": credit,
        "amount_due": amount_due,
        "message": f"Upgrade to {new_tier}. Pay ${amount_due:.2f} (${credit:.2f} credit applied)"
    }


async def cancel_subscription(
    db: AsyncSession,
    user_id: int,
    reason: Optional[str] = None
) -> None:
    """Cancel subscription (remains active until expiry)"""
    subscription = await get_active_subscription(db, user_id)
    if not subscription:
        raise ValueError("No active subscription found")
    
    subscription.auto_renew = False
    subscription.cancelled_at = datetime.utcnow()
    subscription.cancellation_reason = reason
    
    await db.commit()
    logger.info(f"Subscription cancelled for user {user_id}. Expires: {subscription.expires_at}")


async def get_subscription_history(
    db: AsyncSession,
    user_id: int
) -> List[Subscription]:
    """Get all subscriptions for user"""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.started_at.desc())
    )
    return list(result.scalars().all())
