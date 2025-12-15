"""
Pydantic schemas for subscription management
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class SubscriptionTierEnum(str, Enum):
    FREE = "FREE"
    FREELANCER = "FREELANCER"
    OUTLET = "OUTLET"
    ENTERPRISE = "ENTERPRISE"


class PaymentMethod(str, Enum):
    MONERO = "MONERO"
    STRIPE = "STRIPE"


class SubscriptionCreate(BaseModel):
    tier: SubscriptionTierEnum
    payment_method: PaymentMethod = PaymentMethod.MONERO


class SubscriptionUpgrade(BaseModel):
    new_tier: SubscriptionTierEnum


class SubscriptionCancellation(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    tier: SubscriptionTierEnum
    status: str
    started_at: datetime
    expires_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    auto_renew: bool
    
    class Config:
        from_attributes = True
