"""Security headers and CORS middleware."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

from app.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        
        # Content Security Policy - strict for security
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy - no leakage
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # Permissions policy - disable unnecessary features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "microphone=(), payment=(), usb=(), "
            "interest-cohort=()"  # Disable FLoC
        )
        
        # Strict Transport Security (HTTPS only - not for .onion)
        if not request.url.hostname.endswith('.onion'):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        return response


class TorCircuitMiddleware(BaseHTTPMiddleware):
    """Extract and validate Tor circuit information."""
    
    async def dispatch(self, request: Request, call_next):
        circuit_hash = request.headers.get("X-Tor-Circuit-Hash")
        
        if circuit_hash:
            # Store in request state for use by other middleware
            request.state.tor_circuit = circuit_hash
            logger.debug(f"Tor circuit detected: {circuit_hash[:8]}...")
        
        response = await call_next(request)
        return response
