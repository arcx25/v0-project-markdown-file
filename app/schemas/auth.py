"""Authentication schemas."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class RegisterChallengeRequest(BaseModel):
    """Request to initiate registration."""
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    role: str = Field(..., pattern=r"^(buyer|vendor)$")
    public_key: str = Field(..., min_length=100)
    
    @field_validator('public_key')
    @classmethod
    def validate_pgp_key(cls, v: str) -> str:
        if "BEGIN PGP PUBLIC KEY BLOCK" not in v:
            raise ValueError("Invalid PGP public key format")
        return v.strip()


class RegisterChallengeResponse(BaseModel):
    """Response with challenge for registration."""
    challenge: str
    challenge_id: str
    expires_in_seconds: int


class RegisterVerifyRequest(BaseModel):
    """Request to complete registration with signed challenge."""
    challenge_id: str
    signed_challenge: str = Field(..., min_length=100)
    
    # Optional profile data
    organization: Optional[str] = Field(None, max_length=255)
    position: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = Field(None, max_length=5000)
    anonymous_alias: Optional[str] = Field(None, max_length=100)


class RegisterVerifyResponse(BaseModel):
    """Response after successful registration."""
    message: str
    user_id: int
    username: str
    session_token: str


class LoginChallengeRequest(BaseModel):
    """Request to initiate login."""
    username: str = Field(..., min_length=3, max_length=64)


class LoginChallengeResponse(BaseModel):
    """Response with challenge for login."""
    challenge: str
    challenge_id: str
    expires_in_seconds: int
    public_key: str


class LoginVerifyRequest(BaseModel):
    """Request to complete login with signed challenge."""
    challenge_id: str
    signed_challenge: str = Field(..., min_length=100)


class LoginVerifyResponse(BaseModel):
    """Response after successful login."""
    message: str
    user_id: int
    username: str
    role: str
    session_token: str


class LogoutRequest(BaseModel):
    """Request to logout."""
    pass


class SessionResponse(BaseModel):
    """Current session information."""
    user_id: int
    username: str
    role: str
    session_created_at: str
    session_expires_at: str
