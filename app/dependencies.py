"""FastAPI dependencies."""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.pgp_service import PGPService
from app.services.auth_service import AuthService
from app.models.user import User, UserRole


async def get_pgp_service() -> PGPService:
    """Dependency for PGP service."""
    return PGPService()


async def get_auth_service(pgp: PGPService = Depends(get_pgp_service)) -> AuthService:
    """Dependency for auth service."""
    return AuthService(pgp)


def get_circuit_hash(request: Request) -> Optional[str]:
    """Extract circuit hash from request headers (Tor circuit identifier)."""
    # In production, this would come from Tor headers or custom middleware
    return request.headers.get("X-Circuit-Hash")


async def get_current_user(
    request: Request,
    authorization: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Dependency to get current authenticated user."""
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # Get circuit hash
    circuit_hash = get_circuit_hash(request)
    
    # Validate session
    user = await auth_service.validate_session(db, token, circuit_hash)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return user


async def get_current_buyer(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure current user is a buyer."""
    if current_user.role != UserRole.BUYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer access required"
        )
    return current_user


async def get_current_vendor(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure current user is a vendor."""
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vendor access required"
        )
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to ensure current user is an admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
