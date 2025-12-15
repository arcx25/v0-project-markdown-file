"""Price oracle for USD/XMR conversion."""

import httpx
from typing import Optional
from decimal import Decimal
import json

from app.config import get_settings


class PriceOracle:
    """Service for fetching XMR/USD price."""
    
    def __init__(self):
        self.settings = get_settings()
        self.cache_ttl = self.settings.PRICE_CACHE_TTL_SECONDS
        self._cached_price: Optional[Decimal] = None
        self._cache_timestamp: Optional[float] = None
    
    async def get_xmr_price_usd(self) -> Decimal:
        """
        Get current XMR price in USD.
        
        Returns:
            Price as Decimal
        """
        
        # Try CoinGecko first
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price?ids=monero&vs_currencies=usd",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if "monero" in data and "usd" in data["monero"]:
                    return Decimal(str(data["monero"]["usd"]))
        
        except Exception as e:
            print(f"[v0] CoinGecko price fetch failed: {e}")
        
        # Fallback to Kraken
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.kraken.com/0/public/Ticker?pair=XMRUSD",
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if "result" in data and "XXMRZUSD" in data["result"]:
                    price_data = data["result"]["XXMRZUSD"]
                    return Decimal(str(price_data["c"][0]))  # Last trade closed
        
        except Exception as e:
            print(f"[v0] Kraken price fetch failed: {e}")
        
        # Fallback to default price if all APIs fail
        return Decimal("150.00")  # Conservative fallback
    
    def usd_to_xmr(self, usd_amount: int, xmr_price: Decimal) -> int:
        """
        Convert USD to XMR atomic units.
        
        Args:
            usd_amount: Amount in USD cents
            xmr_price: Current XMR price in USD
            
        Returns:
            Amount in XMR atomic units (piconeros)
        """
        
        xmr_amount = Decimal(usd_amount) / xmr_price
        atomic_units = int(xmr_amount * Decimal("1000000000000"))  # 1 XMR = 10^12 atomic units
        
        return atomic_units
    
    def xmr_to_usd(self, atomic_units: int, xmr_price: Decimal) -> int:
        """
        Convert XMR atomic units to USD cents.
        
        Args:
            atomic_units: Amount in XMR atomic units (piconeros)
            xmr_price: Current XMR price in USD
            
        Returns:
            Amount in USD cents
        """
        
        xmr_amount = Decimal(atomic_units) / Decimal("1000000000000")
        usd_cents = int(xmr_amount * xmr_price * 100)
        
        return usd_cents
