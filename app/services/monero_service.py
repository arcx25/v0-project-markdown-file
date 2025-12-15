"""Comprehensive Monero payment service with deposit tracking."""

import httpx
from typing import Optional, Tuple, Dict
from decimal import Decimal
import secrets
import logging
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.payment import Deposit, DepositStatus, DepositPurpose

logger = logging.getLogger(__name__)


class MoneroService:
    """Service for Monero wallet operations and payment tracking."""
    
    def __init__(self):
        self.wallet_rpc_url = settings.MONERO_WALLET_RPC_URL
        self.rpc_user = settings.MONERO_RPC_USER
        self.rpc_password = settings.MONERO_RPC_PASSWORD
    
    async def _rpc_call(self, method: str, params: dict = None) -> dict:
        """Make RPC call to Monero wallet."""
        payload = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method,
            "params": params or {}
        }
        
        auth = None
        if self.rpc_user and self.rpc_password:
            auth = (self.rpc_user, self.rpc_password)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.wallet_rpc_url,
                json=payload,
                auth=auth
            )
            response.raise_for_status()
            return response.json()
    
    def xmr_to_atomic(self, xmr: Decimal) -> int:
        """Convert XMR to atomic units (piconero)."""
        return int(xmr * Decimal(1e12))
    
    def atomic_to_xmr(self, atomic: int) -> Decimal:
        """Convert atomic units to XMR."""
        return Decimal(atomic) / Decimal(1e12)
    
    async def generate_integrated_address(self, payment_id: Optional[str] = None) -> Dict[str, str]:
        """Generate integrated Monero address with payment ID."""
        if not payment_id:
            payment_id = secrets.token_hex(32)
        
        result = await self._rpc_call("make_integrated_address", {
            "payment_id": payment_id
        })
        
        if "result" in result:
            return {
                "integrated_address": result["result"]["integrated_address"],
                "payment_id": payment_id
            }
        
        raise Exception("Failed to generate integrated address")
    
    async def create_deposit_address(
        self,
        db: AsyncSession,
        user_id: str,
        purpose: DepositPurpose,
        expected_amount_atomic: int,
        reference_id: Optional[str] = None,
        expires_hours: int = 24
    ) -> Deposit:
        """Create a new deposit address for user."""
        # Generate payment ID and integrated address
        address_info = await self.generate_integrated_address()
        
        # Create deposit record
        deposit = Deposit(
            user_id=UUID(user_id),
            address=address_info["integrated_address"],
            payment_id=address_info["payment_id"],
            expected_amount_atomic=expected_amount_atomic,
            status=DepositStatus.PENDING,
            purpose=purpose,
            reference_id=reference_id,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours)
        )
        
        db.add(deposit)
        await db.commit()
        await db.refresh(deposit)
        
        logger.info(f"Created deposit address for user {user_id}, purpose {purpose.value}")
        return deposit
    
    async def get_balance(self) -> Tuple[Decimal, Decimal]:
        """Get wallet balance in XMR."""
        result = await self._rpc_call("get_balance")
        
        if "result" in result:
            balance = self.atomic_to_xmr(result["result"]["balance"])
            unlocked = self.atomic_to_xmr(result["result"]["unlocked_balance"])
            return balance, unlocked
        
        return Decimal(0), Decimal(0)
    
    async def get_payments(self, payment_id: str) -> list:
        """Get payments for specific payment ID."""
        result = await self._rpc_call("get_payments", {
            "payment_id": payment_id
        })
        
        if "result" in result and "payments" in result["result"]:
            return result["result"]["payments"]
        
        return []
    
    async def check_payment(
        self,
        payment_id: str,
        expected_amount_atomic: int
    ) -> Tuple[bool, int, int]:
        """Check if payment has been received with required confirmations."""
        payments = await self.get_payments(payment_id)
        
        if not payments:
            return False, 0, 0
        
        total_amount = sum(p["amount"] for p in payments)
        min_confirmations = min(p.get("confirmations", 0) for p in payments)
        
        received = total_amount >= expected_amount_atomic
        
        return received, total_amount, min_confirmations
    
    async def check_deposit_status(
        self,
        db: AsyncSession,
        deposit: Deposit
    ) -> bool:
        """Check and update deposit status. Returns True if status changed."""
        if deposit.status in [DepositStatus.CONFIRMED, DepositStatus.EXPIRED]:
            return False
        
        # Check for expiration
        if datetime.utcnow() > deposit.expires_at:
            deposit.status = DepositStatus.EXPIRED
            await db.commit()
            logger.info(f"Deposit {deposit.id} expired")
            return True
        
        # Check for payment
        received, amount, confirmations = await self.check_payment(
            deposit.payment_id,
            deposit.expected_amount_atomic
        )
        
        if not received:
            return False
        
        # Update deposit with received amount
        if deposit.received_amount_atomic != amount:
            deposit.received_amount_atomic = amount
            deposit.status = DepositStatus.CONFIRMING
            await db.commit()
            logger.info(f"Deposit {deposit.id} received {self.atomic_to_xmr(amount)} XMR, {confirmations} confirmations")
            return True
        
        # Check if confirmed (10+ confirmations)
        if confirmations >= 10 and deposit.status != DepositStatus.CONFIRMED:
            deposit.status = DepositStatus.CONFIRMED
            deposit.confirmed_at = datetime.utcnow()
            await db.commit()
            logger.info(f"Deposit {deposit.id} confirmed with {confirmations} confirmations")
            return True
        
        return False


monero_service = MoneroService()
