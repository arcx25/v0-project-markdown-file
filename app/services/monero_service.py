"""Monero payment service."""

import httpx
from typing import Optional, Tuple
from decimal import Decimal
import secrets

from app.config import get_settings


class MoneroService:
    """Service for Monero wallet operations."""
    
    def __init__(self):
        self.settings = get_settings()
        self.wallet_rpc_url = self.settings.MONERO_WALLET_RPC_URL
        self.rpc_user = self.settings.MONERO_RPC_USER
        self.rpc_password = self.settings.MONERO_RPC_PASSWORD
    
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
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.wallet_rpc_url,
                json=payload,
                auth=auth,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def generate_integrated_address(self, payment_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate an integrated Monero address with payment ID.
        
        Returns:
            Tuple of (integrated_address, payment_id)
        """
        
        if not payment_id:
            # Generate random 64-character payment ID
            payment_id = secrets.token_hex(32)
        
        result = await self._rpc_call("make_integrated_address", {
            "payment_id": payment_id
        })
        
        if "result" in result:
            return result["result"]["integrated_address"], payment_id
        
        raise Exception("Failed to generate integrated address")
    
    async def get_balance(self) -> Tuple[int, int]:
        """
        Get wallet balance.
        
        Returns:
            Tuple of (balance, unlocked_balance) in atomic units
        """
        
        result = await self._rpc_call("get_balance")
        
        if "result" in result:
            return result["result"]["balance"], result["result"]["unlocked_balance"]
        
        return 0, 0
    
    async def get_payments(self, payment_id: str) -> list:
        """Get payments for a specific payment ID."""
        
        result = await self._rpc_call("get_payments", {
            "payment_id": payment_id
        })
        
        if "result" in result and "payments" in result["result"]:
            return result["result"]["payments"]
        
        return []
    
    async def check_payment(
        self,
        payment_id: str,
        expected_amount: int
    ) -> Tuple[bool, int, int]:
        """
        Check if a payment has been received.
        
        Returns:
            Tuple of (received, amount, confirmations)
        """
        
        payments = await self.get_payments(payment_id)
        
        if not payments:
            return False, 0, 0
        
        # Sum all payments with this payment ID
        total_amount = sum(p["amount"] for p in payments)
        
        # Get minimum confirmations across all payments
        min_confirmations = min(p.get("confirmations", 0) for p in payments)
        
        received = total_amount >= expected_amount
        
        return received, total_amount, min_confirmations
