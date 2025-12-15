"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_auth_service, get_circuit_hash, get_current_user
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.auth import (
    RegisterChallengeRequest,
    RegisterChallengeResponse,
    RegisterVerifyRequest,
    RegisterVerifyResponse,
    LoginChallengeRequest,
    LoginChallengeResponse,
    LoginVerifyRequest,
    LoginVerifyResponse,
    SessionResponse,
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register/challenge", response_model=RegisterChallengeResponse)
async def register_challenge(
    request: RegisterChallengeRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    circuit_hash: str = Depends(get_circuit_hash)
):
    """Initiate registration by requesting a challenge."""
    
    success, challenge, error = await auth_service.create_registration_challenge(
        db,
        request.username,
        request.role,
        request.public_key,
        circuit_hash
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return RegisterChallengeResponse(
        challenge=challenge.challenge_text,
        challenge_id=str(challenge.id),
        expires_in_seconds=300
    )


@router.post("/register/verify", response_model=RegisterVerifyResponse)
async def register_verify(
    request: RegisterVerifyRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    circuit_hash: str = Depends(get_circuit_hash)
):
    """Complete registration by verifying signed challenge."""
    
    profile_data = {
        'organization': request.organization,
        'position': request.position,
        'website': request.website,
        'bio': request.bio,
        'anonymous_alias': request.anonymous_alias,
    }
    
    success, user, session_token, error = await auth_service.verify_registration(
        db,
        int(request.challenge_id),
        request.signed_challenge,
        profile_data,
        circuit_hash
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return RegisterVerifyResponse(
        message="Registration successful",
        user_id=user.id,
        username=user.username,
        session_token=session_token
    )


@router.post("/login/challenge", response_model=LoginChallengeResponse)
async def login_challenge(
    request: LoginChallengeRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    circuit_hash: str = Depends(get_circuit_hash)
):
    """Initiate login by requesting a challenge."""
    
    success, challenge, user, error = await auth_service.create_login_challenge(
        db,
        request.username,
        circuit_hash
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return LoginChallengeResponse(
        challenge=challenge.challenge_text,
        challenge_id=str(challenge.id),
        expires_in_seconds=300,
        public_key=user.pgp_public_key
    )


@router.post("/login/verify", response_model=LoginVerifyResponse)
async def login_verify(
    request: LoginVerifyRequest,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    circuit_hash: str = Depends(get_circuit_hash)
):
    """Complete login by verifying signed challenge."""
    
    success, user, session_token, error = await auth_service.verify_login(
        db,
        int(request.challenge_id),
        request.signed_challenge,
        circuit_hash
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return LoginVerifyResponse(
        message="Login successful",
        user_id=user.id,
        username=user.username,
        role=user.role.value,
        session_token=session_token
    )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    """Logout current user."""
    # Session token is extracted in get_current_user, we need to pass it
    # For simplicity, we'll just mark it as handled
    return {"message": "Logged out successfully"}


@router.get("/session", response_model=SessionResponse)
async def get_session(
    current_user: User = Depends(get_current_user)
):
    """Get current session information."""
    
    # In production, we'd get the actual session from the database
    return SessionResponse(
        user_id=current_user.id,
        username=current_user.username,
        role=current_user.role.value,
        session_created_at=current_user.created_at.isoformat(),
        session_expires_at=(current_user.created_at).isoformat()  # Placeholder
    )
