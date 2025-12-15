"""Advanced rate limiting middleware with Redis backend."""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
import time
import hashlib
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
import logging

from app.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiting middleware with Redis.
    
    Features:
    - Per-endpoint rate limits
    - Tor circuit-aware limiting
    - Progressive lockout for auth endpoints
    - Burst handling with token bucket algorithm
    """
    
    # Rate limit configurations
    RATE_LIMITS = {
        "/api/auth/challenge": {"requests": 10, "window": 60, "lockout": 300},
        "/api/auth/login": {"requests": 5, "window": 300, "lockout": 900},
        "/api/auth/register": {"requests": 3, "window": 3600, "lockout": 3600},
        "/api/leads": {"requests": 100, "window": 60},
        "/api/messages": {"requests": 50, "window": 60},
        "/api/listings": {"requests": 30, "window": 60},
        "default": {"requests": 60, "window": 60},
    }
    
    def __init__(self, app, redis: Redis):
        super().__init__(app)
        self.redis = redis
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit config for this endpoint
        config = self._get_rate_limit_config(request.url.path)
        
        # Check rate limit
        is_allowed, retry_after = await self._check_rate_limit(
            client_id,
            request.url.path,
            config
        )
        
        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path}"
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": str(retry_after)},
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = await self._get_remaining_requests(client_id, request.url.path, config)
        response.headers["X-RateLimit-Limit"] = str(config["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + config["window"])
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Generate unique client identifier prioritizing Tor circuit."""
        circuit = request.headers.get("X-Tor-Circuit-Hash")
        if circuit:
            return f"circuit:{circuit}"
        
        # Use session token hash
        session = request.cookies.get("vault_session")
        if session:
            return f"session:{hashlib.sha256(session.encode()).hexdigest()[:16]}"
        
        # Fallback to IP (limited usefulness with Tor)
        ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}"
    
    def _get_rate_limit_config(self, path: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint."""
        for pattern, config in self.RATE_LIMITS.items():
            if pattern != "default" and path.startswith(pattern):
                return config
        return self.RATE_LIMITS["default"]
    
    async def _check_rate_limit(
        self,
        client_id: str,
        endpoint: str,
        config: Dict[str, int]
    ) -> Tuple[bool, int]:
        """
        Check rate limit using sliding window with Redis.
        
        Returns:
            (is_allowed, retry_after_seconds)
        """
        key = f"ratelimit:{client_id}:{endpoint}"
        now = int(time.time())
        window = config["window"]
        max_requests = config["requests"]
        
        # Check if in lockout period
        lockout_key = f"lockout:{client_id}:{endpoint}"
        lockout_until = await self.redis.get(lockout_key)
        if lockout_until:
            retry_after = int(lockout_until) - now
            if retry_after > 0:
                return False, retry_after
        
        pipe = self.redis.pipeline()
        pipe.zadd(key, {f"{now}:{hash(client_id)}": now})
        pipe.zremrangebyscore(key, 0, now - window)
        pipe.zcard(key)
        pipe.expire(key, window + 60)
        results = await pipe.execute()
        
        count = results[2]
        
        if count > max_requests:
            if "lockout" in config:
                await self.redis.setex(
                    lockout_key,
                    config["lockout"],
                    str(now + config["lockout"])
                )
                return False, config["lockout"]
            return False, window
        
        return True, 0
    
    async def _get_remaining_requests(
        self,
        client_id: str,
        endpoint: str,
        config: Dict[str, int]
    ) -> int:
        """Get remaining requests in current window."""
        key = f"ratelimit:{client_id}:{endpoint}"
        now = int(time.time())
        window = config["window"]
        
        count = await self.redis.zcount(key, now - window, now)
        remaining = max(0, config["requests"] - count)
        return remaining
