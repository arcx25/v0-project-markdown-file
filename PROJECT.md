ARCHITECT // VAULT - Complete Technical Summary & Build Guide
Executive Overview
ARCHITECT // VAULT is a secure platform connecting whistleblowers with verified journalists, featuring anonymous source leads, encrypted communications, tiered support listings, and Monero-based donations. The platform operates as a Tor v3 onion service with optional clearnet access for journalists.

System Architecture Diagram
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ARCHITECT // VAULT ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              CLIENT LAYER                                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │   │
│  │  │  Tor Browser │  │   Clearnet   │  │   Mobile     │  │    API       │         │   │
│  │  │   (Sources)  │  │ (Journalists)│  │  (Future)    │  │   Clients    │         │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │   │
│  └─────────┼─────────────────┼─────────────────┼─────────────────┼──────────────────┘   │
│            │                 │                 │                 │                      │
│            ▼                 ▼                 ▼                 ▼                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              EDGE LAYER                                          │   │
│  │  ┌──────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                         Tor Onion Service (v3)                            │   │   │
│  │  │                    56-char .onion address + Vanguards                     │   │   │
│  │  └──────────────────────────────────┬───────────────────────────────────────┘   │   │
│  │                                     │                                            │   │
│  │  ┌──────────────────────────────────┴───────────────────────────────────────┐   │   │
│  │  │                    Caddy Reverse Proxy (TLS 1.3)                          │   │   │
│  │  │              Rate Limiting │ Request Filtering │ Security Headers         │   │   │
│  │  └──────────────────────────────────┬───────────────────────────────────────┘   │   │
│  └─────────────────────────────────────┼────────────────────────────────────────────┘   │
│                                        │                                                │
│                                        ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           APPLICATION LAYER                                      │   │
│  │                                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │   │
│  │  │                      FastAPI Application (Uvicorn)                       │    │   │
│  │  │                     Python 3.11+ │ AsyncIO │ uvloop                      │    │   │
│  │  ├─────────────────────────────────────────────────────────────────────────┤    │   │
│  │  │                                                                          │    │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │    │   │
│  │  │  │    Auth     │ │   Leads     │ │  Messages   │ │  Listings   │        │    │   │
│  │  │  │   Module    │ │   Module    │ │   Module    │ │   Module    │        │    │   │
│  │  │  │ (ARCHITECT) │ │             │ │  (PGP E2E)  │ │  (Support)  │        │    │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │    │   │
│  │  │                                                                          │    │   │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │    │   │
│  │  │  │  Payments   │ │   Admin     │ │Subscriptions│ │  Analytics  │        │    │   │
│  │  │  │   (Monero)  │ │ Moderation  │ │             │ │  (Privacy)  │        │    │   │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘        │    │   │
│  │  │                                                                          │    │   │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐    │   │
│  │  │                      Background Workers (Celery)                         │    │   │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │   │
│  │  │  │ Payment  │ │  Lead    │ │Subscription│ │  Cleanup │ │ Notifier │       │    │   │
│  │  │  │ Monitor  │ │  Expiry  │ │  Renewal  │ │  Worker  │ │  Worker  │       │    │   │
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │    │   │
│  │  └─────────────────────────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                                │
│                                        ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              DATA LAYER                                          │   │
│  │                                                                                   │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐               │   │
│  │  │   PostgreSQL 16  │  │    Redis 7.2     │  │   File Storage   │               │   │
│  │  │   (Primary DB)   │  │  (Cache/Queue)   │  │   (Encrypted)    │               │   │
│  │  │                  │  │                  │  │                  │               │   │
│  │  │ • Users          │  │ • Sessions       │  │ • Media files    │               │   │
│  │  │ • Leads          │  │ • Rate limits    │  │ • Documents      │               │   │
│  │  │ • Messages       │  │ • Challenge cache│  │ • Backups        │               │   │
│  │  │ • Listings       │  │ • Task queue     │  │                  │               │   │
│  │  │ • Contributions  │  │ • Pub/Sub        │  │                  │               │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                                │
│                                        ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           CRYPTO LAYER                                           │   │
│  │                                                                                   │   │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐               │   │
│  │  │   GnuPG 2.4+     │  │    Monerod       │  │  Monero Wallet   │               │   │
│  │  │   (PGP Engine)   │  │  (Full Node)     │  │      RPC         │               │   │
│  │  │                  │  │                  │  │                  │               │   │
│  │  │ • Key management │  │ • Blockchain     │  │ • Address gen    │               │   │
│  │  │ • Encryption     │  │ • Transaction    │  │ • Balance check  │               │   │
│  │  │ • Signatures     │  │   validation     │  │ • Transfers      │               │   │
│  │  │ • Verification   │  │ • P2P network    │  │ • Payment proofs │               │   │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘               │   │
│  └──────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
Technology Stack Summary
Layer	Technology	Purpose
Runtime	Python 3.11+	Core language with asyncio
Framework	FastAPI 0.109+	Async web framework
Server	Uvicorn + uvloop	High-performance ASGI
Database	PostgreSQL 16	Primary data store
Cache	Redis 7.2	Sessions, rate limits, queues
Task Queue	Celery	Background job processing
ORM	SQLAlchemy 2.0	Async database access
Migrations	Alembic	Schema versioning
Templates	Jinja2	Server-side rendering
Crypto	python-gnupg	PGP operations
Payments	monero-python	XMR integration
Proxy	Caddy 2.7	Reverse proxy, TLS
Anonymity	Tor 0.4.8+	Onion service
OS	Debian 12	Hardened server
Core Features Breakdown
1. Authentication (ARCHITECT Protocol)
PGP-based challenge-response authentication
No passwords stored - cryptographic proof of identity
Session binding to Tor circuits
Rate limiting and progressive lockout
2. Lead System
Sources submit anonymized leads (category, scope, evidence types)
Admin moderation before publication
Journalists browse and express interest
Source selects journalist for secure communication
3. Secure Messaging
End-to-end PGP encryption
Messages encrypted to recipient's public key
Platform cannot read message contents
Conversation tied to lead context
4. Support Listings
Sources create public support profiles
Configurable donation tiers with perks
Single-use XMR addresses per contribution
Anonymous supporter wall
Progress tracking and updates
5. Subscription System
Journalist tiers: Free, Freelancer (
50
/
m
o
)
,
O
u
t
l
e
t
(
50/mo),Outlet(500/mo), Enterprise ($2000/mo)
XMR and fiat (Stripe) payment options
Auto-renewal with PGP notifications
6. Admin Moderation
Lead review queue
Journalist verification
Listing approval
User management and suspension
Build Order & Dependencies
Phase 1: Foundation (Week 1-2)
├── Project scaffolding
├── Database schema & migrations
├── Configuration management
├── Basic middleware (rate limiting, sessions)
└── Static assets & base templates

Phase 2: Authentication (Week 3-4)
├── PGP service implementation
├── ARCHITECT protocol
├── Session management
├── User registration/login flows
└── Role-based access control

Phase 3: Core Features (Week 5-7)
├── Lead submission & management
├── Lead browsing for journalists
├── Interest expression & matching
├── Secure messaging system
└── Admin moderation tools

Phase 4: Payments (Week 8-9)
├── Monero node setup
├── Wallet RPC integration
├── Single-use address generation
├── Payment monitoring worker
├── Subscription management

Phase 5: Support Listings (Week 10-11)
├── Listing CRUD operations
├── Tier management
├── Contribution flow
├── Supporter wall
├── Listing updates

Phase 6: Polish & Security (Week 12-13)
├── Security audit
├── Performance optimization
├── Error handling
├── Logging & monitoring
├── Documentation

Phase 7: Deployment (Week 14)
├── Infrastructure provisioning
├── Tor onion service setup
├── SSL/TLS configuration
├── Backup procedures
└── Launch checklist
API Endpoints Summary
Authentication
POST /api/auth/register/challenge    # Initiate registration
POST /api/auth/register/verify       # Complete registration
POST /api/auth/login/challenge       # Initiate login
POST /api/auth/login/verify          # Complete login
POST /api/auth/logout                # End session
GET  /api/auth/session               # Validate session
Leads
POST /api/leads                      # Create lead (source)
GET  /api/leads                      # Browse leads (journalist)
GET  /api/leads/{id}                 # Get lead detail
PUT  /api/leads/{id}                 # Update lead (source)
POST /api/leads/{id}/submit          # Submit for review (source)
POST /api/leads/{id}/interest        # Express interest (journalist)
GET  /api/leads/{id}/interests       # View interests (source)
POST /api/leads/{id}/accept/{journalist_id}  # Accept journalist (source)
Messages
GET  /api/conversations              # List conversations
GET  /api/conversations/{id}         # Get conversation
POST /api/conversations/{id}/messages # Send message
GET  /api/conversations/{id}/messages # Get messages
Support Listings
POST /api/listings                   # Create listing (source)
GET  /api/listings                   # Browse listings (public)
GET  /api/listings/{slug}            # Get listing detail
PUT  /api/listings/{id}              # Update listing (source)
POST /api/listings/{id}/submit       # Submit for review
POST /api/listings/{id}/tiers        # Add tier
PUT  /api/listings/{id}/tiers/{tier_id}  # Update tier
POST /api/listings/{slug}/contribute # Initiate contribution
GET  /api/listings/{id}/supporters   # Get supporters
POST /api/listings/{id}/updates      # Post update (source)
Subscriptions
GET  /api/subscriptions/plans        # Get subscription plans
POST /api/subscriptions              # Create subscription
GET  /api/subscriptions/current      # Get current subscription
POST /api/subscriptions/cancel       # Cancel subscription
Admin
GET  /api/admin/leads/pending        # Pending leads
POST /api/admin/leads/{id}/approve   # Approve lead
POST /api/admin/leads/{id}/reject    # Reject lead
GET  /api/admin/journalists/pending  # Pending verifications
POST /api/admin/journalists/{id}/verify  # Verify journalist
GET  /api/admin/listings/pending     # Pending listings
POST /api/admin/listings/{id}/approve # Approve listing
GET  /api/admin/users                # User management
POST /api/admin/users/{id}/suspend   # Suspend user
Security Measures
Category	Implementation
Authentication	PGP challenge-response, no passwords
Sessions	Cryptographic tokens, circuit binding, sliding expiry
Encryption	E2E PGP for messages, TLS 1.3 in transit, LUKS at rest
Rate Limiting	Per-user, per-circuit, per-endpoint limits
Input Validation	Pydantic schemas, sanitization, length limits
CSRF	SameSite cookies, origin validation
XSS	Jinja2 auto-escaping, CSP headers
SQL Injection	SQLAlchemy ORM, parameterized queries
Privacy	No IP logging, Tor integration, anonymous payments
Audit	Comprehensive logging (anonymized), tamper-evident
Database Schema Summary
Users & Auth
├── users (id, username, role, pgp_fingerprint, pgp_public_key, ...)
├── journalist_profiles (user_id, organization, verification_status, ...)
├── source_profiles (user_id, anonymous_alias, trust_score, ...)
├── auth_challenges (id, username, challenge_hash, attempts, ...)
└── sessions (id, user_id, token_hash, circuit_hash, ...)

Leads & Matching
├── leads (id, source_id, title, category, summary, status, ...)
└── lead_interests (id, lead_id, journalist_id, pitch, status, ...)

Messaging
├── conversations (id, lead_id, source_id, journalist_id, ...)
└── messages (id, conversation_id, sender_id, encrypted_content, ...)

Support Listings
├── support_listings (id, source_id, title, slug, category, story, ...)
├── support_tiers (id, listing_id, name, amount_usd, perks, ...)
├── support_contributions (id, listing_id, tier_id, amount_xmr_atomic, ...)
├── supporter_wall (id, listing_id, display_name, tier_name, ...)
└── listing_updates (id, listing_id, title, content, ...)

Payments
├── deposits (id, user_id, address, payment_id, expected_amount, ...)
└── subscriptions (id, user_id, tier, started_at, expires_at, ...)

System
├── audit_log (id, user_id, action, resource_type, ...)
├── rate_limits (key, count, window_start, expires_at)
└── encrypted_media (id, owner_id, storage_path, ...)
COMPLETE IMPLEMENTATION PROMPT
Below is a comprehensive, production-ready implementation of ARCHITECT // VAULT. This is the largest coherent codebase I can provide in a single response.

# ============================================================================
# ARCHITECT // VAULT - Complete Implementation
# ============================================================================
# 
# Project Structure:
# vault/
# ├── alembic/
# │   ├── versions/
# │   │   └── 001_initial_schema.py
# │   ├── env.py
# │   └── alembic.ini
# ├── app/
# │   ├── __init__.py
# │   ├── main.py
# │   ├── config.py
# │   ├── database.py
# │   ├── dependencies.py
# │   ├── models/
# │   │   ├── __init__.py
# │   │   ├── user.py
# │   │   ├── lead.py
# │   │   ├── message.py
# │   │   ├── listing.py
# │   │   └── payment.py
# │   ├── schemas/
# │   │   ├── __init__.py
# │   │   ├── auth.py
# │   │   ├── user.py
# │   │   ├── lead.py
# │   │   ├── message.py
# │   │   ├── listing.py
# │   │   └── payment.py
# │   ├── services/
# │   │   ├── __init__.py
# │   │   ├── auth_service.py
# │   │   ├── pgp_service.py
# │   │   ├── lead_service.py
# │   │   ├── message_service.py
# │   │   ├── listing_service.py
# │   │   ├── monero_service.py
# │   │   ├── subscription_service.py
# │   │   └── price_oracle.py
# │   ├── api/
# │   │   ├── __init__.py
# │   │   ├── router.py
# │   │   ├── auth.py
# │   │   ├── leads.py
# │   │   ├── messages.py
# │   │   ├── listings.py
# │   │   ├── subscriptions.py
# │   │   └── admin.py
# │   ├── workers/
# │   │   ├── __init__.py
# │   │   ├── celery_app.py
# │   │   ├── payment_monitor.py
# │   │   └── cleanup.py
# │   ├── middleware/
# │   │   ├── __init__.py
# │   │   ├── rate_limiter.py
# │   │   ├── session.py
# │   │   └── security.py
# │   ├── templates/
# │   │   └── [All HTML templates]
# │   └── static/
# │       └── css/
# │           └── vault.css
# ├── deploy/
# │   ├── docker-compose.yml
# │   ├── Dockerfile
# │   └── systemd/
# ├── tests/
# ├── .env.example
# ├── pyproject.toml
# └── README.md
#
# ============================================================================


# ============================================================================
# FILE: pyproject.toml
# ============================================================================
"""
[project]
name = "architect-vault"
version = "1.0.0"
description = "Secure platform connecting whistleblowers with verified journalists"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "uvloop>=0.19.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "redis>=5.0.0",
    "celery>=5.3.0",
    "python-gnupg>=0.5.2",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
    "httpx>=0.26.0",
    "passlib[argon2]>=1.7.4",
    "segno>=1.6.0",
    "pillow>=10.2.0",
    "pyotp>=2.9.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=24.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]
"""


# ============================================================================
# FILE: app/config.py
# ============================================================================
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    # Application
    APP_NAME: str = Field(default="ARCHITECT // VAULT")
    APP_VERSION: str = Field(default="1.0.0")
    SECRET_KEY: str = Field(..., min_length=64)
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://vault:vault@localhost:5432/vault"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # Security
    SESSION_EXPIRE_MINUTES: int = Field(default=30)
    CHALLENGE_EXPIRE_SECONDS: int = Field(default=300)
    MAX_LOGIN_ATTEMPTS: int = Field(default=5)
    LOCKOUT_DURATION_MINUTES: int = Field(default=15)
    
    # PGP
    GNUPG_HOME: str = Field(default="/var/lib/vault/gnupg")
    PLATFORM_PGP_FINGERPRINT: str = Field(...)
    PLATFORM_PGP_PASSPHRASE: Optional[str] = Field(default=None)
    
    # Monero
    MONERO_WALLET_RPC_URL: str = Field(default="http://127.0.0.1:18082/json_rpc")
    MONERO_WALLET_RPC_USER: str = Field(default="rpc_user")
    MONERO_WALLET_RPC_PASSWORD: str = Field(...)
    MONERO_CONFIRMATIONS_REQUIRED: int = Field(default=10)
    
    # Hostnames
    ONION_HOSTNAME: str = Field(...)
    CLEARNET_HOSTNAME: Optional[str] = Field(default=None)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_AUTH_ATTEMPTS: int = Field(default=5)
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=900)
    
    # Subscription Pricing (USD cents)
    PRICE_FREELANCER_MONTHLY: int = Field(default=5000)
    PRICE_OUTLET_MONTHLY: int = Field(default=50000)
    PRICE_ENTERPRISE_MONTHLY: int = Field(default=200000)
    
    # Fees
    DONATION_FEE_PERCENT: float = Field(default=7.5)
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# ============================================================================
# FILE: app/database.py
# ============================================================================
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import AsyncGenerator

from app.config import settings


# Naming convention for constraints
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    
    # Common columns
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection."""
    async with engine.begin() as conn:
        # Tables created via Alembic migrations
        pass


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


# ============================================================================
# FILE: app/models/__init__.py
# ============================================================================
from app.models.user import (
    User,
    UserRole,
    JournalistProfile,
    SourceProfile,
    VerificationStatus,
    AuthChallenge,
    Session,
)
from app.models.lead import (
    Lead,
    LeadStatus,
    LeadCategory,
    EvidenceType,
    LeadInterest,
    InterestStatus,
)
from app.models.message import (
    Conversation,
    Message,
)
from app.models.listing import (
    SupportListing,
    ListingStatus,
    ListingCategory,
    SupportTier,
    SupportContribution,
    ContributionStatus,
    SupporterWall,
    ListingUpdate,
)
from app.models.payment import (
    Deposit,
    DepositStatus,
    DepositPurpose,
    Subscription,
    SubscriptionTier,
    SubscriptionStatus,
)

__all__ = [
    "User",
    "UserRole",
    "JournalistProfile",
    "SourceProfile",
    "VerificationStatus",
    "AuthChallenge",
    "Session",
    "Lead",
    "LeadStatus",
    "LeadCategory",
    "EvidenceType",
    "LeadInterest",
    "InterestStatus",
    "Conversation",
    "Message",
    "SupportListing",
    "ListingStatus",
    "ListingCategory",
    "SupportTier",
    "SupportContribution",
    "ContributionStatus",
    "SupporterWall",
    "ListingUpdate",
    "Deposit",
    "DepositStatus",
    "DepositPurpose",
    "Subscription",
    "SubscriptionTier",
    "SubscriptionStatus",
]


# ============================================================================
# FILE: app/models/user.py
# ============================================================================
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    SOURCE = "source"
    JOURNALIST = "journalist"
    ADMIN = "admin"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class User(Base):
    """Core user model with PGP authentication."""
    
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), nullable=False)
    pgp_fingerprint: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    pgp_public_key: Mapped[str] = mapped_column(Text, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    threat_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    journalist_profile: Mapped[Optional["JournalistProfile"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
    source_profile: Mapped[Optional["SourceProfile"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
    sessions: Mapped[List["Session"]] = relationship(back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"


class JournalistProfile(Base):
    """Extended profile for journalist users."""
    
    __tablename__ = "journalist_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organization_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    beat: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="journalist_profile")
    
    @property
    def is_subscribed(self) -> bool:
        if self.subscription_tier == "free":
            return True
        if not self.subscription_expires_at:
            return False
        return self.subscription_expires_at > datetime.now(timezone.utc)


class SourceProfile(Base):
    """Extended profile for source users."""
    
    __tablename__ = "source_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    anonymous_alias: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    industry_hint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="source_profile")


class AuthChallenge(Base):
    """PGP authentication challenges."""
    
    __tablename__ = "auth_challenges"
    
    username: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    challenge_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)


class Session(Base):
    """User sessions with Tor circuit binding."""
    
    __tablename__ = "sessions"
    
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    circuit_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")


# ============================================================================
# FILE: app/models/lead.py
# ============================================================================
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import enum

from app.database import Base


class LeadStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PUBLISHED = "published"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class LeadCategory(str, enum.Enum):
    GOVERNMENT_MISCONDUCT = "government_misconduct"
    CORPORATE_FRAUD = "corporate_fraud"
    ENVIRONMENTAL = "environmental"
    HUMAN_RIGHTS = "human_rights"
    PUBLIC_HEALTH = "public_health"
    FINANCIAL_CRIMES = "financial_crimes"
    SURVEILLANCE_PRIVACY = "surveillance_privacy"
    MILITARY_INTELLIGENCE = "military_intelligence"
    OTHER = "other"


class EvidenceType(str, enum.Enum):
    DOCUMENTS = "documents"
    COMMUNICATIONS = "communications"
    FINANCIAL_RECORDS = "financial_records"
    MULTIMEDIA = "multimedia"
    TESTIMONY = "testimony"
    TECHNICAL_DATA = "technical_data"
    OTHER = "other"


class InterestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Lead(Base):
    """Whistleblower lead submissions."""
    
    __tablename__ = "leads"
    
    source_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Public information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[LeadCategory] = mapped_column(SQLEnum(LeadCategory), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_types: Mapped[List[str]] = mapped_column(ARRAY(String(50)), nullable=False)
    geographic_scope: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    time_sensitivity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Status & workflow
    status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus), default=LeadStatus.DRAFT
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Review
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Matching
    matched_journalist_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Completion
    publication_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    interests: Mapped[List["LeadInterest"]] = relationship(back_populates="lead")


class LeadInterest(Base):
    """Journalist interest in leads."""
    
    __tablename__ = "lead_interests"
    
    lead_id: Mapped[UUID] = mapped_column(ForeignKey("leads.id"), nullable=False)
    journalist_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    pitch: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InterestStatus] = mapped_column(
        SQLEnum(InterestStatus), default=InterestStatus.PENDING
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    lead: Mapped["Lead"] = relationship(back_populates="interests")


# ============================================================================
# FILE: app/models/message.py
# ============================================================================
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from app.database import Base


class Conversation(Base):
    """Secure conversation between source and journalist."""
    
    __tablename__ = "conversations"
    
    lead_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("leads.id"), nullable=True
    )
    source_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    journalist_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    last_message_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    closed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation")


class Message(Base):
    """End-to-end encrypted message."""
    
    __tablename__ = "messages"
    
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id"), nullable=False
    )
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # PGP encrypted content
    encrypted_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


# ============================================================================
# FILE: app/models/listing.py
# ============================================================================
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
import enum

from app.database import Base


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class ListingCategory(str, enum.Enum):
    WHISTLEBLOWER_PROTECTION = "whistleblower_protection"
    LEGAL_DEFENSE = "legal_defense"
    RELOCATION_SAFETY = "relocation_safety"
    FAMILY_SUPPORT = "family_support"
    SECURE_INFRASTRUCTURE = "secure_infrastructure"
    JOURNALISM_FUNDING = "journalism_funding"
    RESEARCH_INVESTIGATION = "research_investigation"
    GENERAL_SUPPORT = "general_support"


class ContributionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SupportListing(Base):
    """Public support listing for sources."""
    
    __tablename__ = "support_listings"
    
    source_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Public information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    category: Mapped[ListingCategory] = mapped_column(
        SQLEnum(ListingCategory), nullable=False
    )
    headline: Mapped[str] = mapped_column(String(300), nullable=False)
    story: Mapped[str] = mapped_column(Text, nullable=False)
    
    disclosure_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Goals
    funding_goal_usd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    funding_deadline: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Verification
    verified_by_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    # Status & metrics
    status: Mapped[ListingStatus] = mapped_column(
        SQLEnum(ListingStatus), default=ListingStatus.DRAFT
    )
    total_raised_atomic: Mapped[int] = mapped_column(BigInteger, default=0)
    supporter_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    closes_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    tiers: Mapped[List["SupportTier"]] = relationship(back_populates="listing")
    contributions: Mapped[List["SupportContribution"]] = relationship(
        back_populates="listing"
    )
    supporters: Mapped[List["SupporterWall"]] = relationship(back_populates="listing")
    updates: Mapped[List["ListingUpdate"]] = relationship(back_populates="listing")


class SupportTier(Base):
    """Configurable support tier for a listing."""
    
    __tablename__ = "support_tiers"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_listings.id"), nullable=False
    )
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount_usd: Mapped[int] = mapped_column(Integer, nullable=False)  # Cents
    
    perks: Mapped[Optional[List]] = mapped_column(JSONB, default=list)
    is_highlighted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    max_supporters: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_supporters: Mapped[int] = mapped_column(Integer, default=0)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="tiers")
    
    @property
    def is_available(self) -> bool:
        if not self.max_supporters:
            return True
        return self.current_supporters < self.max_supporters
    
    @property
    def spots_remaining(self) -> Optional[int]:
        if not self.max_supporters:
            return None
        return self.max_supporters - self.current_supporters


class SupportContribution(Base):
    """Individual contribution to a listing."""
    
    __tablename__ = "support_contributions"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_listings.id"), nullable=False
    )
    tier_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("support_tiers.id"), nullable=True
    )
    
    # Supporter info
    supporter_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    supporter_alias: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Payment
    amount_usd_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_xmr_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exchange_rate_used: Mapped[str] = mapped_column(String(20), nullable=False)
    
    deposit_id: Mapped[UUID] = mapped_column(ForeignKey("deposits.id"), nullable=False)
    
    # Message
    encrypted_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Status
    status: Mapped[ContributionStatus] = mapped_column(
        SQLEnum(ContributionStatus), default=ContributionStatus.PENDING
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tx_confirmations: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="contributions")


class SupporterWall(Base):
    """Public supporter recognition."""
    
    __tablename__ = "supporter_wall"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_listings.id"), nullable=False
    )
    contribution_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_contributions.id"), unique=True, nullable=False
    )
    
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    tier_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    amount_display: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    show_amount: Mapped[bool] = mapped_column(Boolean, default=False)
    
    public_message: Mapped[Optional[str]] = mapped_column(String(280), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="supporters")


class ListingUpdate(Base):
    """Progress updates from source."""
    
    __tablename__ = "listing_updates"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("support_listings.id"), nullable=False
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    minimum_tier_amount: Mapped[int] = mapped_column(Integer, default=0)
    
    media_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(36)), nullable=True)
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="updates")


# ============================================================================
# FILE: app/models/payment.py
# ============================================================================
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from uuid import UUID
import enum

from app.database import Base


class DepositStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    FAILED = "failed"


class DepositPurpose(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    TOP_UP = "top_up"
    ORDER = "order"
    SUPPORT_CONTRIBUTION = "support_contribution"
    VENDOR_UPGRADE = "vendor_upgrade"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    FREELANCER = "freelancer"
    OUTLET = "outlet"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRING = "expiring"
    GRACE_PERIOD = "grace_period"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Deposit(Base):
    """Single-use Monero deposit addresses."""
    
    __tablename__ = "deposits"
    
    user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    
    address: Mapped[str] = mapped_column(String(106), unique=True, nullable=False)
    payment_id: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    
    expected_amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    received_amount_atomic: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    purpose: Mapped[DepositPurpose] = mapped_column(
        SQLEnum(DepositPurpose), nullable=False
    )
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    status: Mapped[DepositStatus] = mapped_column(
        SQLEnum(DepositStatus), default=DepositStatus.PENDING
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    tx_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=0)
    
    qr_code_base64: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Subscription(Base):
    """Journalist subscription management."""
    
    __tablename__ = "subscriptions"
    
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    tier: Mapped[SubscriptionTier] = mapped_column(
        SQLEnum(SubscriptionTier), nullable=False
    )
    
    price_usd_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    price_xmr_atomic: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


# ============================================================================
# FILE: app/schemas/auth.py
# ============================================================================
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class RegisterRequest(BaseModel):
    """Registration initiation request."""
    
    username: str = Field(..., min_length=3, max_length=32)
    role: str = Field(..., pattern="^(source|journalist)$")
    pgp_public_key: str = Field(..., min_length=100)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must be alphanumeric with underscores only")
        
        reserved = {
            "admin", "administrator", "root", "system", "support",
            "help", "info", "contact", "security", "moderator", "vault", "architect"
        }
        if v.lower() in reserved:
            raise ValueError("This username is reserved")
        
        return v.lower()
    
    @field_validator("pgp_public_key")
    @classmethod
    def validate_pgp_key(cls, v: str) -> str:
        if "-----BEGIN PGP PUBLIC KEY BLOCK-----" not in v:
            raise ValueError("Invalid PGP public key format")
        if "-----END PGP PUBLIC KEY BLOCK-----" not in v:
            raise ValueError("Invalid PGP public key format")
        return v


class RegisterChallengeResponse(BaseModel):
    """Challenge response for registration/login."""
    
    encrypted_challenge: str
    signature: str
    server_fingerprint: str
    expires_in_seconds: int


class ChallengeResponseRequest(BaseModel):
    """User's response to authentication challenge."""
    
    username: str = Field(..., min_length=3, max_length=32)
    challenge_response: str = Field(..., min_length=50)
    
    @field_validator("challenge_response")
    @classmethod
    def validate_response(cls, v: str) -> str:
        if not v.startswith("ARCHITECT_"):
            raise ValueError("Invalid challenge response format")
        return v


class LoginRequest(BaseModel):
    """Login initiation request."""
    
    username: str = Field(..., min_length=3, max_length=32)


class AuthResponse(BaseModel):
    """Successful authentication response."""
    
    success: bool
    session_token: str
    user_id: str
    username: str
    role: str
    expires_in_seconds: int


class SessionInfo(BaseModel):
    """Current session information."""
    
    user_id: str
    username: str
    role: str
    expires_at: str


# ============================================================================
# FILE: app/schemas/lead.py
# ============================================================================
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class LeadCreateRequest(BaseModel):
    """Lead creation request."""
    
    title: str = Field(..., min_length=10, max_length=200)
    category: str = Field(...)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    summary: str = Field(..., min_length=200, max_length=2000)
    evidence_types: List[str] = Field(..., min_length=1)
    geographic_scope: Optional[List[str]] = Field(default=None)
    time_sensitivity: Optional[str] = Field(
        default=None, pattern="^(urgent|moderate|archival)$"
    )
    
    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        # Check for PII patterns (basic)
        import re
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}"
        phone_pattern = r"bd{3}[-.]?d{3}[-.]?d{4}b"
        
        if re.search(email_pattern, v):
            raise ValueError("Please do not include email addresses in the summary")
        if re.search(phone_pattern, v):
            raise ValueError("Please do not include phone numbers in the summary")
        
        return v


class LeadResponse(BaseModel):
    """Lead response model."""
    
    id: str
    title: str
    category: str
    subcategory: Optional[str]
    summary: str
    evidence_types: List[str]
    geographic_scope: Optional[List[str]]
    time_sensitivity: Optional[str]
    status: str
    submitted_at: Optional[str]
    created_at: str


class LeadListResponse(BaseModel):
    """Paginated lead list response."""
    
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LeadInterestRequest(BaseModel):
    """Journalist interest expression."""
    
    pitch: str = Field(..., min_length=50, max_length=1000)


class LeadInterestResponse(BaseModel):
    """Interest response for sources."""
    
    interest_id: str
    journalist_username: str
    organization: Optional[str]
    organization_verified: bool
    beat: Optional[List[str]]
    pitch: str
    created_at: str


# ============================================================================
# FILE: app/schemas/listing.py
# ============================================================================
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class TierCreateRequest(BaseModel):
    """Support tier creation request."""
    
    name: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=20, max_length=500)
    amount_usd: int = Field(..., ge=100)  # Minimum $1 (100 cents)
    perks: Optional[List[str]] = Field(default=None)
    is_highlighted: bool = Field(default=False)
    max_supporters: Optional[int] = Field(default=None, ge=1)


class ListingCreateRequest(BaseModel):
    """Listing creation request."""
    
    title: str = Field(..., min_length=10, max_length=200)
    category: str = Field(...)
    headline: str = Field(..., min_length=50, max_length=300)
    story: str = Field(..., min_length=500, max_length=10000)
    disclosure_summary: Optional[str] = Field(default=None, max_length=1000)
    risk_description: Optional[str] = Field(default=None, max_length=1000)
    funding_goal_usd: Optional[int] = Field(default=None, ge=100)
    funding_deadline: Optional[datetime] = Field(default=None)


class ListingResponse(BaseModel):
    """Listing response model."""
    
    id: str
    slug: str
    title: str
    category: str
    headline: str
    story: str
    disclosure_summary: Optional[str]
    risk_description: Optional[str]
    funding_goal_usd: Optional[int]
    total_raised_xmr: str
    supporter_count: int
    view_count: int
    progress_percent: int
    verified: bool
    status: str
    created_at: str
    published_at: Optional[str]


class TierResponse(BaseModel):
    """Tier response model."""
    
    id: str
    name: str
    description: str
    amount_usd: int
    amount_display: str
    perks: List[str]
    is_highlighted: bool
    spots_remaining: Optional[int]
    is_available: bool


class ContributionCreateRequest(BaseModel):
    """Contribution initiation request."""
    
    supporter_alias: Optional[str] = Field(default=None, max_length=64)
    is_anonymous: bool = Field(default=True)
    message: Optional[str] = Field(default=None, max_length=1000)


class ContributionResponse(BaseModel):
    """Contribution payment details."""
    
    contribution_id: str
    listing_title: str
    tier_name: str
    amount_usd: str
    amount_xmr: str
    xmr_address: str
    payment_id: str
    qr_code_base64: Optional[str]
    expires_at: str
    exchange_rate: str


class SupporterResponse(BaseModel):
    """Public supporter info."""
    
    display_name: str
    tier_name: Optional[str]
    amount_display: Optional[str]
    public_message: Optional[str]
    is_featured: bool
    created_at: str


class ListingDetailResponse(BaseModel):
    """Full listing detail with tiers and supporters."""
    
    listing: ListingResponse
    tiers: List[TierResponse]
    supporters: List[SupporterResponse]
    updates: List[dict]


# ============================================================================
# FILE: app/schemas/message.py
# ============================================================================
from pydantic import BaseModel, Field
from typing import Optional, List


class ConversationResponse(BaseModel):
    """Conversation summary."""
    
    id: str
    lead_id: Optional[str]
    lead_title: Optional[str]
    other_party_username: str
    other_party_role: str
    last_message_at: Optional[str]
    unread_count: int
    is_closed: bool


class MessageCreateRequest(BaseModel):
    """Send message request."""
    
    encrypted_content: str = Field(..., min_length=50)
    content_hash: str = Field(..., min_length=64, max_length=64)


class MessageResponse(BaseModel):
    """Message response."""
    
    id: str
    sender_username: str
    is_mine: bool
    encrypted_content: str
    content_hash: str
    created_at: str
    read_at: Optional[str]


class ConversationDetailResponse(BaseModel):
    """Full conversation with messages."""
    
    conversation: ConversationResponse
    messages: List[MessageResponse]
    recipient_pgp_fingerprint: str
    recipient_pgp_public_key: str


# ============================================================================
# FILE: app/services/pgp_service.py
# ============================================================================
import gnupg
import secrets
import hashlib
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from app.config import settings


class PGPKeyAlgorithm(Enum):
    ED25519 = "ed25519"
    CURVE25519 = "curve25519"
    RSA4096 = "rsa4096"
    RSA2048 = "rsa2048"
    DSA = "dsa"


@dataclass
class PGPKeyInfo:
    """Validated PGP key information."""
    
    fingerprint: str
    algorithm: PGPKeyAlgorithm
    key_length: int
    user_ids: list
    expires_at: Optional[int]
    is_revoked: bool
    is_valid: bool
    rejection_reason: Optional[str] = None


class PGPService:
    """PGP cryptographic operations service."""
    
    def __init__(self):
        self.gpg = gnupg.GPG(gnupghome=settings.GNUPG_HOME)
        self.gpg.encoding = "utf-8"
    
    def validate_public_key(self, armored_key: str) -> PGPKeyInfo:
        """
        Validate a PGP public key for registration.
        Accepts: Ed25519, Curve25519, RSA 4096+
        Rejects: DSA, RSA < 4096, expired, revoked
        """
        # Import key temporarily
        import_result = self.gpg.import_keys(armored_key)
        
        if not import_result.fingerprints:
            return PGPKeyInfo(
                fingerprint="",
                algorithm=PGPKeyAlgorithm.RSA2048,
                key_length=0,
                user_ids=[],
                expires_at=None,
                is_revoked=False,
                is_valid=False,
                rejection_reason="Invalid PGP key format - could not parse",
            )
        
        fingerprint = import_result.fingerprints[0]
        keys = self.gpg.list_keys(keys=[fingerprint])
        
        if not keys:
            self._cleanup_key(fingerprint)
            return PGPKeyInfo(
                fingerprint=fingerprint,
                algorithm=PGPKeyAlgorithm.RSA2048,
                key_length=0,
                user_ids=[],
                expires_at=None,
                is_revoked=False,
                is_valid=False,
                rejection_reason="Could not retrieve key details after import",
            )
        
        key = keys[0]
        
        # Determine algorithm
        algo = key.get("algo", "").lower()
        key_length = int(key.get("length", 0))
        
        if "ed25519" in algo or key.get("algo") == "22":
            algorithm = PGPKeyAlgorithm.ED25519
        elif "cv25519" in algo or "curve25519" in algo:
            algorithm = PGPKeyAlgorithm.CURVE25519
        elif "rsa" in algo or key.get("algo") in ["1", "2", "3"]:
            algorithm = PGPKeyAlgorithm.RSA4096 if key_length >= 4096 else PGPKeyAlgorithm.RSA2048
        elif "dsa" in algo or key.get("algo") == "17":
            algorithm = PGPKeyAlgorithm.DSA
        else:
            algorithm = PGPKeyAlgorithm.RSA2048
        
        # Check expiration
        expires_at = None
        if key.get("expires"):
            expires_at = int(key["expires"])
        
        # Check revocation
        is_revoked = key.get("trust", "") == "r"
        
        # Validation rules
        rejection_reason = None
        is_valid = True
        
        if algorithm == PGPKeyAlgorithm.DSA:
            is_valid = False
            rejection_reason = "DSA keys are not accepted. Please use Ed25519 or RSA-4096+"
        elif algorithm == PGPKeyAlgorithm.RSA2048:
            is_valid = False
            rejection_reason = f"RSA keys must be at least 4096 bits. Your key is {key_length} bits."
        elif is_revoked:
            is_valid = False
            rejection_reason = "This key has been revoked"
        elif expires_at and expires_at < time.time() + (30 * 24 * 60 * 60):
            is_valid = False
            rejection_reason = "Key expires within 30 days. Please use a longer-lived key."
        
        # Clean up if invalid
        if not is_valid:
            self._cleanup_key(fingerprint)
        
        return PGPKeyInfo(
            fingerprint=fingerprint,
            algorithm=algorithm,
            key_length=key_length,
            user_ids=key.get("uids", []),
            expires_at=expires_at,
            is_revoked=is_revoked,
            is_valid=is_valid,
            rejection_reason=rejection_reason,
        )
    
    def generate_challenge(self, username: str) -> Tuple[str, str]:
        """
        Generate an ARCHITECT challenge for authentication.
        Returns: (challenge_plaintext, challenge_hash)
        """
        token = secrets.token_urlsafe(48)  # 384 bits entropy
        timestamp = int(time.time())
        server_fp_short = settings.PLATFORM_PGP_FINGERPRINT[:8].upper()
        
        challenge = f"ARCHITECT_{token}_{timestamp}_{server_fp_short}"
        challenge_hash = hashlib.sha256(challenge.encode()).hexdigest()
        
        return challenge, challenge_hash
    
    def encrypt_challenge(self, challenge: str, recipient_fingerprint: str) -> str:
        """Encrypt a challenge to the user's public key."""
        encrypted = self.gpg.encrypt(
            challenge,
            recipients=[recipient_fingerprint],
            armor=True,
            always_trust=True,
        )
        
        if not encrypted.ok:
            raise ValueError(f"PGP encryption failed: {encrypted.status}")
        
        return str(encrypted)
    
    def sign_message(self, message: str) -> str:
        """Sign a message with the platform's private key."""
        signed = self.gpg.sign(
            message,
            keyid=settings.PLATFORM_PGP_FINGERPRINT,
            passphrase=settings.PLATFORM_PGP_PASSPHRASE,
            detach=True,
            armor=True,
        )
        
        if not signed:
            raise ValueError("PGP signing failed")
        
        return str(signed)
    
    def encrypt_message(
        self,
        plaintext: str,
        recipient_fingerprint: str,
        sign: bool = True,
    ) -> str:
        """
        Encrypt a message for secure communication.
        Optionally sign with platform key.
        """
        kwargs = {
            "recipients": [recipient_fingerprint],
            "armor": True,
            "always_trust": True,
        }
        
        if sign:
            kwargs["sign"] = settings.PLATFORM_PGP_FINGERPRINT
            kwargs["passphrase"] = settings.PLATFORM_PGP_PASSPHRASE
        
        encrypted = self.gpg.encrypt(plaintext, **kwargs)
        
        if not encrypted.ok:
            raise ValueError(f"PGP encryption failed: {encrypted.status}")
        
        return str(encrypted)
    
    def verify_challenge_response(
        self,
        response: str,
        expected_hash: str,
        max_age_seconds: int = 300,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify an ARCHITECT challenge response.
        Returns: (is_valid, error_message)
        """
        # Check format
        parts = response.split("_")
        if len(parts) != 4:
            return False, "Invalid challenge format: expected 4 parts"
        
        if parts[0] != "ARCHITECT":
            return False, "Invalid challenge format: must start with ARCHITECT"
        
        # Verify hash (constant-time comparison)
        response_hash = hashlib.sha256(response.encode()).hexdigest()
        if not secrets.compare_digest(response_hash, expected_hash):
            return False, "Challenge response does not match"
        
        # Verify timestamp
        try:
            timestamp = int(parts[2])
            age = time.time() - timestamp
            
            # Allow 60s clock skew in either direction
            if age > max_age_seconds:
                return False, "Challenge has expired"
            if age < -60:
                return False, "Challenge timestamp is in the future"
        except ValueError:
            return False, "Invalid timestamp in challenge"
        
        # Verify server fingerprint
        expected_fp = settings.PLATFORM_PGP_FINGERPRINT[:8].upper()
        if parts[3].upper() != expected_fp:
            return False, "Invalid server fingerprint in challenge"
        
        return True, None
    
    def _cleanup_key(self, fingerprint: str) -> bool:
        """Remove a key from the keyring."""
        try:
            self.gpg.delete_keys(fingerprint)
            return True
        except Exception:
            return False


# Singleton instance
pgp_service = PGPService()


# ============================================================================
# FILE: app/services/auth_service.py
# ============================================================================
import secrets
import hashlib
import asyncio
import random
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.config import settings
from app.models.user import (
    User, UserRole, JournalistProfile, SourceProfile,
    AuthChallenge, Session
)
from app.services.pgp_service import pgp_service
from app.schemas.auth import (
    RegisterRequest, RegisterChallengeResponse,
    ChallengeResponseRequest, AuthResponse,
)


class AuthenticationError(Exception):
    """Authentication failure with HTTP status code."""
    
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    """ARCHITECT protocol authentication service."""
    
    def __init__(self, db: AsyncSession, redis: Redis):
        self.db = db
        self.redis = redis
    
    async def initiate_registration(
        self,
        request: RegisterRequest,
    ) -> RegisterChallengeResponse:
        """
        Registration Step 1: Validate key and issue encrypted challenge.
        """
        # Check rate limit
        await self._check_rate_limit(f"register:{request.username}")
        
        # Check username availability
        existing = await self.db.execute(
            select(User).where(User.username == request.username)
        )
        if existing.scalar_one_or_none():
            raise AuthenticationError("Username already taken", status_code=409)
        
        # Validate PGP key
        key_info = pgp_service.validate_public_key(request.pgp_public_key)
        
        if not key_info.is_valid:
            raise AuthenticationError(
                key_info.rejection_reason or "Invalid PGP key",
                status_code=422,
            )
        
        # Check fingerprint uniqueness
        existing_fp = await self.db.execute(
            select(User).where(User.pgp_fingerprint == key_info.fingerprint)
        )
        if existing_fp.scalar_one_or_none():
            raise AuthenticationError(
                "This PGP key is already registered with another account",
                status_code=409,
            )
        
        # Generate challenge
        challenge_plain, challenge_hash = pgp_service.generate_challenge(
            request.username
        )
        
        # Encrypt to user's key
        encrypted_challenge = pgp_service.encrypt_challenge(
            challenge_plain,
            key_info.fingerprint,
        )
        
        # Sign our response
        signature = pgp_service.sign_message(encrypted_challenge)
        
        # Store challenge
        auth_challenge = AuthChallenge(
            username=request.username,
            challenge_hash=challenge_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(
                seconds=settings.CHALLENGE_EXPIRE_SECONDS
            ),
        )
        self.db.add(auth_challenge)
        await self.db.flush()
        
        # Store pending registration in Redis
        await self.redis.setex(
            f"pending_reg:{request.username}",
            settings.CHALLENGE_EXPIRE_SECONDS,
            f"{key_info.fingerprint}x00{request.pgp_public_key}x00{request.role}",
        )
        
        return RegisterChallengeResponse(
            encrypted_challenge=encrypted_challenge,
            signature=signature,
            server_fingerprint=settings.PLATFORM_PGP_FINGERPRINT,
            expires_in_seconds=settings.CHALLENGE_EXPIRE_SECONDS,
        )
    
    async def complete_registration(
        self,
        username: str,
        challenge_response: str,
    ) -> AuthResponse:
        """
        Registration Step 2: Verify response and create account.
        """
        username = username.lower()
        
        # Get pending challenge
        result = await self.db.execute(
            select(AuthChallenge)
            .where(AuthChallenge.username == username)
            .where(AuthChallenge.consumed == False)
            .where(AuthChallenge.expires_at > datetime.now(timezone.utc))
            .order_by(AuthChallenge.created_at.desc())
        )
        challenge = result.scalar_one_or_none()
        
        if not challenge:
            raise AuthenticationError(
                "No pending challenge found. Please restart registration.",
                status_code=410,
            )
        
        # Check attempts
        if challenge.attempts >= settings.MAX_LOGIN_ATTEMPTS:
            raise AuthenticationError(
                "Too many failed attempts. Please restart registration.",
                status_code=429,
            )
        
        # Increment attempts
        challenge.attempts += 1
        await self.db.flush()
        
        # Verify response
        is_valid, error = pgp_service.verify_challenge_response(
            challenge_response,
            challenge.challenge_hash,
        )
        
        if not is_valid:
            await self._artificial_delay()
            raise AuthenticationError(error or "Invalid challenge response")
        
        # Mark challenge as consumed
        challenge.consumed = True
        
        # Get pending registration data
        pending_data = await self.redis.get(f"pending_reg:{username}")
        if not pending_data:
            raise AuthenticationError(
                "Registration session expired. Please restart.",
                status_code=410,
            )
        
        fingerprint, pgp_key, role = pending_data.decode().split("x00", 2)
        
        # Create user
        user = User(
            username=username,
            role=UserRole(role),
            pgp_fingerprint=fingerprint,
            pgp_public_key=pgp_key,
        )
        self.db.add(user)
        await self.db.flush()
        
        # Create role-specific profile
        if role == "journalist":
            profile = JournalistProfile(id=user.id)
            self.db.add(profile)
        elif role == "source":
            alias = await self._generate_anonymous_alias()
            profile = SourceProfile(id=user.id, anonymous_alias=alias)
            self.db.add(profile)
        
        # Clean up Redis
        await self.redis.delete(f"pending_reg:{username}")
        
        # Create session
        session_token = await self._create_session(user.id)
        
        return AuthResponse(
            success=True,
            session_token=session_token,
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
            expires_in_seconds=settings.SESSION_EXPIRE_MINUTES * 60,
        )
    
    async def initiate_login(self, username: str) -> RegisterChallengeResponse:
        """
        Login Step 1: Issue challenge to existing user.
        """
        username = username.lower()
        
        # Check rate limit
        await self._check_rate_limit(f"login:{username}")
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if user exists
            await self._artificial_delay()
            raise AuthenticationError("Authentication failed")
        
        if not user.is_active:
            raise AuthenticationError("Account suspended", status_code=403)
        
        # Generate challenge
        challenge_plain, challenge_hash = pgp_service.generate_challenge(username)
        
        # Encrypt to user's key
        encrypted_challenge = pgp_service.encrypt_challenge(
            challenge_plain,
            user.pgp_fingerprint,
        )
        
        signature = pgp_service.sign_message(encrypted_challenge)
        
        # Store challenge
        auth_challenge = AuthChallenge(
            username=username,
            challenge_hash=challenge_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(
                seconds=settings.CHALLENGE_EXPIRE_SECONDS
            ),
        )
        self.db.add(auth_challenge)
        
        return RegisterChallengeResponse(
            encrypted_challenge=encrypted_challenge,
            signature=signature,
            server_fingerprint=settings.PLATFORM_PGP_FINGERPRINT,
            expires_in_seconds=settings.CHALLENGE_EXPIRE_SECONDS,
        )
    
    async def complete_login(
        self,
        username: str,
        challenge_response: str,
        circuit_hash: Optional[str] = None,
    ) -> AuthResponse:
        """
        Login Step 2: Verify challenge and create session.
        """
        username = username.lower()
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await self._artificial_delay()
            raise AuthenticationError("Authentication failed")
        
        # Get challenge
        result = await self.db.execute(
            select(AuthChallenge)
            .where(AuthChallenge.username == username)
            .where(AuthChallenge.consumed == False)
            .where(AuthChallenge.expires_at > datetime.now(timezone.utc))
            .order_by(AuthChallenge.created_at.desc())
        )
        challenge = result.scalar_one_or_none()
        
        if not challenge:
            raise AuthenticationError("No pending challenge", status_code=410)
        
        if challenge.attempts >= settings.MAX_LOGIN_ATTEMPTS:
            raise AuthenticationError("Too many attempts", status_code=429)
        
        challenge.attempts += 1
        await self.db.flush()
        
        # Verify
        is_valid, error = pgp_service.verify_challenge_response(
            challenge_response,
            challenge.challenge_hash,
        )
        
        if not is_valid:
            await self._artificial_delay()
            raise AuthenticationError(error or "Invalid challenge response")
        
        challenge.consumed = True
        
        # Update last seen
        user.last_seen_at = datetime.now(timezone.utc)
        
        # Create session
        session_token = await self._create_session(user.id, circuit_hash)
        
        return AuthResponse(
            success=True,
            session_token=session_token,
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
            expires_in_seconds=settings.SESSION_EXPIRE_MINUTES * 60,
        )
    
    async def validate_session(
        self,
        token: str,
        circuit_hash: Optional[str] = None,
    ) -> Optional[User]:
        """Validate session token and return user."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        result = await self.db.execute(
            select(Session)
            .where(Session.token_hash == token_hash)
            .where(Session.expires_at > datetime.now(timezone.utc))
        )
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Update activity & extend expiry (sliding window)
        session.last_activity_at = datetime.now(timezone.utc)
        session.expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.SESSION_EXPIRE_MINUTES
        )
        
        # Get user
        result = await self.db.execute(
            select(User).where(User.id == session.user_id)
        )
        return result.scalar_one_or_none()
    
    async def logout(self, token: str) -> bool:
        """Invalidate session."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        await self.db.execute(
            delete(Session).where(Session.token_hash == token_hash)
        )
        
        return True
    
    # Private helpers
    
    async def _create_session(
        self,
        user_id: UUID,
        circuit_hash: Optional[str] = None,
    ) -> str:
        """Create a new session."""
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        session = Session(
            user_id=user_id,
            token_hash=token_hash,
            circuit_hash=circuit_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(
                minutes=settings.SESSION_EXPIRE_MINUTES
            ),
        )
        self.db.add(session)
        
        return token
    
    async def _check_rate_limit(self, key: str) -> None:
        """Check and increment rate limit."""
        redis_key = f"ratelimit:{key}"
        count = await self.redis.incr(redis_key)
        
        if count == 1:
            await self.redis.expire(redis_key, settings.RATE_LIMIT_WINDOW_SECONDS)
        
        if count > settings.RATE_LIMIT_AUTH_ATTEMPTS:
            raise AuthenticationError(
                "Too many attempts. Please try again later.",
                status_code=429,
            )
    
    async def _artificial_delay(self) -> None:
        """Add delay to prevent timing attacks."""
        delay = 0.5 + random.random() * 0.5
        await asyncio.sleep(delay)
    
    async def _generate_anonymous_alias(self) -> str:
        """Generate unique anonymous alias for sources."""
        adjectives = [
            "Silent", "Midnight", "Shadow", "Crimson", "Azure",
            "Phantom", "Velvet", "Crystal", "Thunder", "Ember",
            "Frost", "Neon", "Cipher", "Void", "Quantum",
            "Stellar", "Onyx", "Apex", "Nova", "Pulse",
        ]
        nouns = [
            "Raven", "Wolf", "Phoenix", "Falcon", "Serpent",
            "Cipher", "Echo", "Specter", "Horizon", "Nexus",
            "Prism", "Vertex", "Oracle", "Sentinel", "Vector",
            "Vortex", "Zenith", "Architect", "Guardian", "Wanderer",
        ]
        
        for _ in range(100):  # Max attempts
            alias = f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(100, 999)}"
            
            # Check uniqueness
            result = await self.db.execute(
                select(SourceProfile).where(SourceProfile.anonymous_alias == alias)
            )
            if not result.scalar_one_or_none():
                return alias
        
        # Fallback with more entropy
        return f"Source{secrets.token_hex(6)}"


# ============================================================================
# FILE: app/services/monero_service.py
# ============================================================================
import httpx
import secrets
import io
import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import uuid4

import segno
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.payment import Deposit, DepositStatus, DepositPurpose


class MoneroRPCError(Exception):
    """Monero wallet RPC error."""
    
    def __init__(self, message: str, code: int = -1):
        self.message = message
        self.code = code
        super().__init__(message)


class MoneroService:
    """Monero wallet RPC integration service."""
    
    def __init__(self):
        self.rpc_url = settings.MONERO_WALLET_RPC_URL
        self.auth = (
            settings.MONERO_WALLET_RPC_USER,
            settings.MONERO_WALLET_RPC_PASSWORD,
        )
    
    async def _rpc_call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make JSON-RPC call to monero-wallet-rpc."""
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": method,
        }
        
        if params:
            payload["params"] = params
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.rpc_url,
                json=payload,
                auth=self.auth,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        if "error" in data:
            raise MoneroRPCError(
                data["error"].get("message", "Unknown RPC error"),
                data["error"].get("code", -1),
            )
        
        return data.get("result", {})
    
    async def create_deposit_address(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        purpose: DepositPurpose,
        expected_amount_atomic: int,
        reference_id: Optional[str] = None,
        expires_hours: int = 24,
    ) -> Deposit:
        """
        Generate a single-use integrated address for deposit.
        """
        # Generate random 8-byte payment ID
        payment_id = secrets.token_hex(8)
        
        # Call wallet RPC to create integrated address
        result = await self._rpc_call(
            "make_integrated_address",
            {"payment_id": payment_id},
        )
        
        integrated_address = result["integrated_address"]
        
        # Generate QR code
        qr = segno.make(f"monero:{integrated_address}")
        buffer = io.BytesIO()
        qr.save(buffer, kind="png", scale=6, border=2)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Create deposit record
        deposit = Deposit(
            user_id=user_id,
            address=integrated_address,
            payment_id=payment_id,
            expected_amount_atomic=expected_amount_atomic,
            purpose=purpose,
            reference_id=reference_id,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours),
            qr_code_base64=qr_base64,
        )
        
        db.add(deposit)
        await db.flush()
        await db.refresh(deposit)
        
        return deposit
    
    async def get_transfers(
        self,
        account_index: int = 0,
        include_pool: bool = True,
    ) -> Dict[str, Any]:
        """Get incoming transfers for payment detection."""
        return await self._rpc_call(
            "get_transfers",
            {
                "in": True,
                "pending": True,
                "pool": include_pool,
                "account_index": account_index,
            },
        )
    
    async def get_balance(self, account_index: int = 0) -> Dict[str, int]:
        """Get wallet balance."""
        result = await self._rpc_call(
            "get_balance",
            {"account_index": account_index},
        )
        return {
            "balance": result.get("balance", 0),
            "unlocked_balance": result.get("unlocked_balance", 0),
        }
    
    async def transfer(
        self,
        destinations: list,
        account_index: int = 0,
        priority: int = 1,
    ) -> Dict[str, Any]:
        """
        Send XMR to destinations.
        destinations: [{"address": "...", "amount": atomic_units}, ...]
        """
        return await self._rpc_call(
            "transfer",
            {
                "destinations": destinations,
                "account_index": account_index,
                "priority": priority,
                "get_tx_key": True,
            },
        )
    
    def atomic_to_xmr(self, atomic: int) -> Decimal:
        """Convert piconeros to XMR."""
        return Decimal(atomic) / Decimal(1e12)
    
    def xmr_to_atomic(self, xmr: Decimal) -> int:
        """Convert XMR to piconeros."""
        return int(xmr * Decimal(1e12))


# Singleton instance
monero_service = MoneroService()


# ============================================================================
# FILE: app/services/price_oracle.py
# ============================================================================
import httpx
import asyncio
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
import statistics


class PriceOracleError(Exception):
    """Price oracle failure."""
    pass


class PriceOracle:
    """XMR/USD price aggregation service."""
    
    def __init__(self):
        self.cache_ttl_seconds = 300  # 5 minutes
        self._cached_price: Optional[Decimal] = None
        self._cache_timestamp: Optional[datetime] = None
    
    async def get_xmr_usd_price(self) -> Decimal:
        """
        Get current XMR/USD price from multiple sources.
        Returns median price for manipulation resistance.
        """
        # Check cache
        if self._is_cache_valid():
            return self._cached_price
        
        prices = []
        
        # Fetch from multiple sources concurrently
        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = [
                self._fetch_coingecko(client),
                self._fetch_kraken(client),
                self._fetch_binance(client),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Decimal) and result > 0:
                    prices.append(result)
        
        if not prices:
            # Fallback to cached price if available
            if self._cached_price:
                return self._cached_price
            raise PriceOracleError("Could not fetch XMR price from any source")
        
        # Use median for manipulation resistance
        median_price = Decimal(str(statistics.median([float(p) for p in prices])))
        
        # Update cache
        self._cached_price = median_price
        self._cache_timestamp = datetime.now(timezone.utc)
        
        return median_price
    
    def _is_cache_valid(self) -> bool:
        if not self._cached_price or not self._cache_timestamp:
            return False
        
        age = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
        return age < self.cache_ttl_seconds
    
    async def _fetch_coingecko(self, client: httpx.AsyncClient) -> Optional[Decimal]:
        try:
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "monero", "vs_currencies": "usd"},
            )
            response.raise_for_status()
            data = response.json()
            return Decimal(str(data["monero"]["usd"]))
        except Exception:
            return None
    
    async def _fetch_kraken(self, client: httpx.AsyncClient) -> Optional[Decimal]:
        try:
            response = await client.get(
                "https://api.kraken.com/0/public/Ticker",
                params={"pair": "XMRUSD"},
            )
            response.raise_for_status()
            data = response.json()
            price = data["result"]["XXMRZUSD"]["c"][0]
            return Decimal(price)
        except Exception:
            return None
    
    async def _fetch_binance(self, client: httpx.AsyncClient) -> Optional[Decimal]:
        try:
            response = await client.get(
                "https://api.binance.com/api/v3/ticker/price",
                params={"symbol": "XMRUSDT"},
            )
            response.raise_for_status()
            data = response.json()
            return Decimal(data["price"])
        except Exception:
            return None


# Singleton instance
price_oracle = PriceOracle()


# ============================================================================
# FILE: app/api/router.py
# ============================================================================
from fastapi import APIRouter

from app.api import auth, leads, messages, listings, subscriptions, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(leads.router, prefix="/leads", tags=["Leads"])
api_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_router.include_router(listings.router, prefix="/listings", tags=["Support Listings"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])


# ============================================================================
# FILE: app/api/auth.py
# ============================================================================
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import get_db
from app.dependencies import get_redis
from app.services.auth_service import AuthService, AuthenticationError
from app.schemas.auth import (
    RegisterRequest,
    RegisterChallengeResponse,
    ChallengeResponseRequest,
    LoginRequest,
    AuthResponse,
)


router = APIRouter()


@router.post("/register/challenge", response_model=RegisterChallengeResponse)
async def initiate_registration(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    ARCHITECT Protocol Step 1: Submit credentials and receive encrypted challenge.
    
    The challenge is encrypted to your PGP public key. Decrypt it locally
    and submit the plaintext response to complete registration.
    """
    service = AuthService(db, redis)
    
    try:
        return await service.initiate_registration(request)
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/register/verify", response_model=AuthResponse)
async def complete_registration(
    request: ChallengeResponseRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    ARCHITECT Protocol Step 2: Submit decrypted challenge to create account.
    """
    service = AuthService(db, redis)
    
    try:
        result = await service.complete_registration(
            request.username,
            request.challenge_response,
        )
        
        # Set session cookie
        response.set_cookie(
            key="vault_session",
            value=result.session_token,
            max_age=result.expires_in_seconds,
            httponly=True,
            secure=True,
            samesite="strict",
        )
        
        return result
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/login/challenge", response_model=RegisterChallengeResponse)
async def initiate_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    ARCHITECT Protocol Login Step 1: Request challenge for existing account.
    """
    service = AuthService(db, redis)
    
    try:
        return await service.initiate_login(request.username)
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/login/verify", response_model=AuthResponse)
async def complete_login(
    request: ChallengeResponseRequest,
    http_request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    ARCHITECT Protocol Login Step 2: Submit challenge response to authenticate.
    """
    service = AuthService(db, redis)
    
    # Extract Tor circuit hash if available
    circuit_hash = http_request.headers.get("X-Tor-Circuit-Hash")
    
    try:
        result = await service.complete_login(
            request.username,
            request.challenge_response,
            circuit_hash,
        )
        
        response.set_cookie(
            key="vault_session",
            value=result.session_token,
            max_age=result.expires_in_seconds,
            httponly=True,
            secure=True,
            samesite="strict",
        )
        
        return result
    except AuthenticationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    End current session and clear authentication cookie.
    """
    token = request.cookies.get("vault_session")
    
    if token:
        service = AuthService(db, redis)
        await service.logout(token)
    
    response.delete_cookie("vault_session")
    
    return {"success": True, "message":
