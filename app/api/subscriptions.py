"""
Subscription API endpoints for vendor subscription management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user, require_vendor
from app.models.user import User, VendorProfile
from app.models.payment import Subscription, SubscriptionTier
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpgrade,
    SubscriptionCancellation
)
from app.services import subscription_service

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/tiers", response_model=List[dict])
async def get_subscription_tiers():
    """Get available subscription tiers for vendors"""
    return [
        {
            "tier": "FREE",
            "price_usd": 0,
            "price_xmr": 0,
            "features": [
                "View public leads",
                "Express interest in 5 leads/month",
                "Basic profile",
                "Email support"
            ]
        },
        {
            "tier": "FREELANCER",
            "price_usd": 50,
            "price_xmr": None,  # Calculated dynamically
            "features": [
                "Everything in Free",
                "Express interest in 50 leads/month",
                "Enhanced profile with verification badge",
                "Priority support",
                "Advanced search filters"
            ]
        },
        {
            "tier": "OUTLET",
            "price_usd": 500,
            "price_xmr": None,
            "features": [
                "Everything in Freelancer",
                "Unlimited lead interests",
                "Organization profile",
                "Team collaboration (up to 10 users)",
                "API access",
                "Dedicated account manager"
            ]
        },
        {
            "tier": "ENTERPRISE",
            "price_usd": 2000,
            "price_xmr": None,
            "features": [
                "Everything in Outlet",
                "Custom integrations",
                "Unlimited team members",
                "White-label options",
                "24/7 priority support",
                "Custom SLA"
            ]
        }
    ]


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(require_vendor),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's subscription status"""
    subscription = await subscription_service.get_active_subscription(
        db, current_user.id
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    return subscription


@router.post("/subscribe", response_model=dict)
async def create_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(require_vendor),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate subscription to a paid tier
    Returns payment instructions with XMR address
    """
    # Check for existing active subscription
    existing = await subscription_service.get_active_subscription(
        db, current_user.id
    )
    if existing and existing.tier != SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active subscription. Cancel it first or use upgrade endpoint."
        )
    
    payment_info = await subscription_service.create_subscription(
        db, current_user.id, data.tier, data.payment_method
    )
    return payment_info


@router.post("/upgrade", response_model=dict)
async def upgrade_subscription(
    data: SubscriptionUpgrade,
    current_user: User = Depends(require_vendor),
    db: AsyncSession = Depends(get_db)
):
    """Upgrade to a higher subscription tier"""
    current_sub = await subscription_service.get_active_subscription(
        db, current_user.id
    )
    if not current_sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found. Use /subscribe instead."
        )
    
    payment_info = await subscription_service.upgrade_subscription(
        db, current_user.id, data.new_tier
    )
    return payment_info


@router.post("/cancel")
async def cancel_subscription(
    data: SubscriptionCancellation,
    current_user: User = Depends(require_vendor),
    db: AsyncSession = Depends(get_db)
):
    """Cancel current subscription (takes effect at end of billing period)"""
    await subscription_service.cancel_subscription(
        db, current_user.id, data.reason
    )
    return {
        "message": "Subscription cancelled successfully. Access will continue until end of billing period."
    }


@router.get("/history", response_model=List[SubscriptionResponse])
async def get_subscription_history(
    current_user: User = Depends(require_vendor),
    db: AsyncSession = Depends(get_db)
):
    """Get subscription history for current user"""
    history = await subscription_service.get_subscription_history(
        db, current_user.id
    )
    return history
