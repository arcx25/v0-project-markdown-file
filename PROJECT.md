ARCHITECT // VAULT - Complete Technical Summary & Build Guide

## Executive Overview

# ARCHITECT // VAULT - Anonymous XMR Marketplace Platform
ARCHITECT // VAULT is an anonymous marketplace platform connecting buyers with verified vendors, featuring opportunity leads, encrypted communications, tiered vendor listings, and Monero-based payments. The platform operates as a Tor v3 onion service for maximum anonymity.

## System Architecture Diagram

\`\`\`
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              ARCHITECT // VAULT                                          │
│                         Anonymous XMR Marketplace Platform                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│   │   Buyers    │    │   Vendors   │    │   Admins    │    │   Public    │              │
│   │  (Seekers)  │    │ (Providers) │    │(Moderators) │    │  (Browse)   │              │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘              │
│          │                  │                  │                  │                      │
│          └──────────────────┴──────────────────┴──────────────────┘                      │
│                                      │                                                   │
│                              ┌───────▼───────┐                                           │
│                              │  Tor Network  │                                           │
│                              │   (.onion)    │                                           │
│                              └───────┬───────┘                                           │
│                                      │                                                   │
│   ┌──────────────────────────────────▼──────────────────────────────────┐               │
│   │                        FastAPI Application                           │               │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │               │
│   │  │    Auth     │  │   Leads     │  │  Listings   │  │  Messages  │  │               │
│   │  │   (PGP)     │  │(Marketplace)│  │  (Vendor)   │  │(Encrypted) │  │               │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │               │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │               │
│   │  │   Admin     │  │Subscriptions│  │   Monero    │  │   Rate     │  │               │
│   │  │Moderation   │  │  (Tiers)    │  │  Payments   │  │  Limiter   │  │               │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │               │
│   └──────────────────────────────────┬──────────────────────────────────┘               │
│                                      │                                                   │
│          ┌───────────────────────────┼───────────────────────────┐                      │
│          │                           │                           │                      │
│   ┌──────▼──────┐            ┌───────▼───────┐           ┌───────▼───────┐              │
│   │ PostgreSQL  │            │    Redis      │           │    Celery     │              │
│   │  Database   │            │    Cache      │           │   Workers     │              │
│   └─────────────┘            └───────────────┘           └───────────────┘              │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
\`\`\`

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.11+ / FastAPI | Async API framework |
| Database | PostgreSQL 16 | Primary data store |
| Cache | Redis 7.2 | Sessions, rate limits, queues |
| Task Queue | Celery | Background job processing |
| ORM | SQLAlchemy 2.0 | Async database access |
| Migrations | Alembic | Schema versioning |
| Templates | Jinja2 | Server-side rendering |
| Crypto | python-gnupg | PGP operations |
| Payments | monero-python | XMR integration |
| Proxy | Caddy 2.7 | Reverse proxy, TLS |
| Anonymity | Tor 0.4.8+ | Onion service |
| OS | Debian 12 | Hardened server |

## Core Features Breakdown

### 1. Authentication (ARCHITECT Protocol)
- PGP-based challenge-response authentication
- No passwords stored - cryptographic proof of identity
- Session binding to Tor circuits
- Rate limiting and progressive lockout

### 2. Opportunity System (Marketplace)
- Buyers submit opportunity requests (category, scope, requirements)
- Admin moderation before publication
- Vendors browse and express interest
- Buyer selects vendor for secure communication

### 3. Secure Messaging
- End-to-end PGP encryption
- Messages encrypted to recipient's public key
- Platform cannot read message contents
- Conversation tied to opportunity context

### 4. Vendor Listings
- Vendors create public profiles with services
- Configurable pricing tiers
- Single-use XMR addresses per transaction
- Anonymous review system
- Progress tracking and updates

### 5. Subscription System
- Vendor tiers: Free, Basic ($50/mo), Pro ($150/mo), Enterprise ($500/mo)
- Each tier unlocks additional features
- XMR-only payments via integrated addresses
- Automatic renewal tracking

## User Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| BUYER | Seekers looking for goods/services | Post opportunities, browse vendors, make payments |
| VENDOR | Providers of goods/services | Respond to opportunities, create listings, receive payments |
| ADMIN | Platform moderators | Review content, verify vendors, manage users |

## Database Schema

\`\`\`python
# User roles
class UserRole(str, enum.Enum):
    BUYER = "buyer"
    VENDOR = "vendor"
    ADMIN = "admin"

# Vendor verification status
class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

# Vendor profile
class VendorProfile(Base):
    """Extended profile for vendor users."""
    
    __tablename__ = "vendor_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    shop_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

# Buyer profile
class BuyerProfile(Base):
    """Extended profile for buyer users."""
    
    __tablename__ = "buyer_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    anonymous_alias: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
\`\`\`

## API Endpoints

### Authentication
\`\`\`
POST /api/auth/register          # Register with PGP key
POST /api/auth/challenge         # Get auth challenge
POST /api/auth/verify            # Verify signed challenge
POST /api/auth/logout            # End session
\`\`\`

### Opportunities (Marketplace)
\`\`\`
POST /api/leads                      # Create opportunity (buyer)
GET  /api/leads                      # Browse opportunities (vendor)
GET  /api/leads/{id}                 # View opportunity details
PUT  /api/leads/{id}                 # Update opportunity (buyer)
POST /api/leads/{id}/submit          # Submit for review (buyer)
POST /api/leads/{id}/interest        # Express interest (vendor)
GET  /api/leads/{id}/interests       # View interests (buyer)
POST /api/leads/{id}/accept/{vendor_id}  # Accept vendor (buyer)
\`\`\`

### Vendor Listings
\`\`\`
POST /api/listings                   # Create listing (vendor)
GET  /api/listings                   # Browse listings
GET  /api/listings/{id}              # View listing details
PUT  /api/listings/{id}              # Update listing (vendor)
POST /api/listings/{id}/submit       # Submit for review (vendor)
\`\`\`

### Messages
\`\`\`
GET  /api/messages/conversations     # List conversations
GET  /api/messages/{conversation_id} # Get messages
POST /api/messages/{conversation_id} # Send encrypted message
\`\`\`

### Subscriptions
\`\`\`
GET  /api/subscriptions/plans        # View subscription plans
POST /api/subscriptions/subscribe    # Subscribe to plan
GET  /api/subscriptions/current      # Get current subscription
POST /api/subscriptions/cancel       # Cancel subscription
\`\`\`

### Admin
\`\`\`
GET  /api/admin/leads/pending        # Pending opportunities
POST /api/admin/leads/{id}/approve   # Approve opportunity
POST /api/admin/leads/{id}/reject    # Reject opportunity
GET  /api/admin/vendors/pending      # Pending vendor verifications
POST /api/admin/vendors/{id}/verify  # Verify vendor
POST /api/admin/vendors/{id}/reject  # Reject vendor
GET  /api/admin/users                # List all users
POST /api/admin/users/{id}/suspend   # Suspend user
\`\`\`

## Security Features

1. **PGP Authentication** - No passwords, cryptographic identity only
2. **End-to-End Encryption** - Messages encrypted client-side
3. **Tor Hidden Service** - .onion address for anonymity
4. **Rate Limiting** - Redis-backed with role-based limits
5. **CSRF Protection** - Token-based form protection
6. **Input Validation** - Strict validation on all inputs
7. **SQL Injection Prevention** - Parameterized queries via SQLAlchemy
8. **XSS Prevention** - Jinja2 auto-escaping

## Monero Integration

- **Single-use addresses** - Each transaction gets unique subaddress
- **Payment monitoring** - Celery workers check for confirmations
- **Price oracle** - Multi-source XMR/USD conversion
- **Escrow support** - Funds held until transaction complete

## Deployment

The platform is deployed to a dedicated server with:
- Tor hidden service configuration
- PostgreSQL database
- Redis cache
- Celery workers
- Monero daemon (optional, can use remote node)
- Systemd service management

See DEPLOY_NOW.md for complete deployment instructions.
\`\`\`

## Technology Stack Summary
| Layer	| Technology	| Purpose	|
|---|---|---|
| Runtime	| Python 3.11+	| Core language with asyncio	|
| Framework	| FastAPI 0.109+	| Async web framework	|
| Server	| Uvicorn + uvloop	| High-performance ASGI	|
| Database	| PostgreSQL 16	| Primary data store	|
| Cache	| Redis 7.2	| Sessions, rate limits, queues	|
| Task Queue	| Celery	| Background job processing	|
| ORM	| SQLAlchemy 2.0	| Async database access	|
| Migrations	| Alembic	| Schema versioning	|
| Templates	| Jinja2	| Server-side rendering	|
| Crypto	| python-gnupg	| PGP operations	|
| Payments	| monero-python	| XMR integration	|
| Proxy	| Caddy 2.7	| Reverse proxy, TLS	|
| Anonymity	| Tor 0.4.8+	| Onion service	|
| OS	| Debian 12	| Hardened server	|

## Core Features Breakdown

1. Authentication (ARCHITECT Protocol)
PGP-based challenge-response authentication
No passwords stored - cryptographic proof of identity
Session binding to Tor circuits
Rate limiting and progressive lockout

2. Opportunity System (Marketplace)
Buyers submit opportunity requests (category, scope, requirements)
Admin moderation before publication
Vendors browse and express interest
Buyer selects vendor for secure communication

3. Secure Messaging
End-to-end PGP encryption
Messages encrypted to recipient's public key
Platform cannot read message contents
Conversation tied to opportunity context

4. Vendor Listings
Vendors create public profiles with services
Configurable pricing tiers
Single-use XMR addresses per transaction
Anonymous review system
Progress tracking and updates

5. Subscription System
Vendor tiers: Free, Basic ($50/mo), Pro ($150/mo), Enterprise ($500/mo)
Each tier unlocks additional features
XMR-only payments via integrated addresses
Automatic renewal tracking

## User Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| BUYER | Seekers looking for goods/services | Post opportunities, browse vendors, make payments |
| VENDOR | Providers of goods/services | Respond to opportunities, create listings, receive payments |
| ADMIN | Platform moderators | Review content, verify vendors, manage users |

## Database Schema

\`\`\`python
# User roles
class UserRole(str, enum.Enum):
    BUYER = "buyer"
    VENDOR = "vendor"
    ADMIN = "admin"

# Vendor verification status
class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

# Vendor profile
class VendorProfile(Base):
    """Extended profile for vendor users."""
    
    __tablename__ = "vendor_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    shop_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

# Buyer profile
class BuyerProfile(Base):
    """Extended profile for buyer users."""
    
    __tablename__ = "buyer_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    anonymous_alias: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
\`\`\`

## API Endpoints

### Authentication
\`\`\`
POST /api/auth/register          # Register with PGP key
POST /api/auth/challenge         # Get auth challenge
POST /api/auth/verify            # Verify signed challenge
POST /api/auth/logout            # End session
\`\`\`

### Opportunities (Marketplace)
\`\`\`
POST /api/leads                      # Create opportunity (buyer)
GET  /api/leads                      # Browse opportunities (vendor)
GET  /api/leads/{id}                 # View opportunity details
PUT  /api/leads/{id}                 # Update opportunity (buyer)
POST /api/leads/{id}/submit          # Submit for review (buyer)
POST /api/leads/{id}/interest        # Express interest (vendor)
GET  /api/leads/{id}/interests       # View interests (buyer)
POST /api/leads/{id}/accept/{vendor_id}  # Accept vendor (buyer)
\`\`\`

### Vendor Listings
\`\`\`
POST /api/listings                   # Create listing (vendor)
GET  /api/listings                   # Browse listings
GET  /api/listings/{id}              # View listing details
PUT  /api/listings/{id}              # Update listing (vendor)
POST /api/listings/{id}/submit       # Submit for review (vendor)
\`\`\`

### Messages
\`\`\`
GET  /api/messages/conversations     # List conversations
GET  /api/messages/{conversation_id} # Get messages
POST /api/messages/{conversation_id} # Send encrypted message
\`\`\`

### Subscriptions
\`\`\`
GET  /api/subscriptions/plans        # View subscription plans
POST /api/subscriptions/subscribe    # Subscribe to plan
GET  /api/subscriptions/current      # Get current subscription
POST /api/subscriptions/cancel       # Cancel subscription
\`\`\`

### Admin
\`\`\`
GET  /api/admin/leads/pending        # Pending opportunities
POST /api/admin/leads/{id}/approve   # Approve opportunity
POST /api/admin/leads/{id}/reject    # Reject opportunity
GET  /api/admin/vendors/pending      # Pending vendor verifications
POST /api/admin/vendors/{id}/verify  # Verify vendor
POST /api/admin/vendors/{id}/reject  # Reject vendor
GET  /api/admin/users                # List all users
POST /api/admin/users/{id}/suspend   # Suspend user
\`\`\`

## Security Features

1. **PGP Authentication** - No passwords, cryptographic identity only
2. **End-to-End Encryption** - Messages encrypted client-side
3. **Tor Hidden Service** - .onion address for anonymity
4. **Rate Limiting** - Redis-backed with role-based limits
5. **CSRF Protection** - Token-based form protection
6. **Input Validation** - Strict validation on all inputs
7. **SQL Injection Prevention** - Parameterized queries via SQLAlchemy
8. **XSS Prevention** - Jinja2 auto-escaping

## Monero Integration

- **Single-use addresses** - Each transaction gets unique subaddress
- **Payment monitoring** - Celery workers check for confirmations
- **Price oracle** - Multi-source XMR/USD conversion
- **Escrow support** - Funds held until transaction complete

## Deployment

The platform is deployed to a dedicated server with:
- Tor hidden service configuration
- PostgreSQL database
- Redis cache
- Celery workers
- Monero daemon (optional, can use remote node)
- Systemd service management

See DEPLOY_NOW.md for complete deployment instructions.
\`\`\`
| Layer	| Technology	| Purpose	|
|---|---|---|
| Runtime	| Python 3.11+	| Core language with asyncio	|
| Framework	| FastAPI 0.109+	| Async web framework	|
| Server	| Uvicorn + uvloop	| High-performance ASGI	|
| Database	| PostgreSQL 16	| Primary data store	|
| Cache	| Redis 7.2	| Sessions, rate limits, queues	|
| Task Queue	| Celery	| Background job processing	|
| ORM	| SQLAlchemy 2.0	| Async database access	|
| Migrations	| Alembic	| Schema versioning	|
| Templates	| Jinja2	| Server-side rendering	|
| Crypto	| python-gnupg	| PGP operations	|
| Payments	| monero-python	| XMR integration	|
| Proxy	| Caddy 2.7	| Reverse proxy, TLS	|
| Anonymity	| Tor 0.4.8+	| Onion service	|
| OS	| Debian 12	| Hardened server	|

## Core Features Breakdown

1. Authentication (ARCHITECT Protocol)
PGP-based challenge-response authentication
No passwords stored - cryptographic proof of identity
Session binding to Tor circuits
Rate limiting and progressive lockout

2. Opportunity System (Marketplace)
Buyers submit opportunity requests (category, scope, requirements)
Admin moderation before publication
Vendors browse and express interest
Buyer selects vendor for secure communication

3. Secure Messaging
End-to-end PGP encryption
Messages encrypted to recipient's public key
Platform cannot read message contents
Conversation tied to opportunity context

4. Vendor Listings
Vendors create public profiles with services
Configurable pricing tiers
Single-use XMR addresses per transaction
Anonymous review system
Progress tracking and updates

5. Subscription System
Vendor tiers: Free, Basic ($50/mo), Pro ($150/mo), Enterprise ($500/mo)
Each tier unlocks additional features
XMR-only payments via integrated addresses
Automatic renewal tracking

## User Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| BUYER | Seekers looking for goods/services | Post opportunities, browse vendors, make payments |
| VENDOR | Providers of goods/services | Respond to opportunities, create listings, receive payments |
| ADMIN | Platform moderators | Review content, verify vendors, manage users |

## Database Schema

\`\`\`python
# User roles
class UserRole(str, enum.Enum):
    BUYER = "buyer"
    VENDOR = "vendor"
    ADMIN = "admin"

# Vendor verification status
class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

# Vendor profile
class VendorProfile(Base):
    """Extended profile for vendor users."""
    
    __tablename__ = "vendor_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    shop_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free")
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)

# Buyer profile
class BuyerProfile(Base):
    """Extended profile for buyer users."""
    
    __tablename__ = "buyer_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    anonymous_alias: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    trust_score: Mapped[int] = mapped_column(Integer, default=50)
\`\`\`

## API Endpoints

### Authentication
\`\`\`
POST /api/auth/register          # Register with PGP key
POST /api/auth/challenge         # Get auth challenge
POST /api/auth/verify            # Verify signed challenge
POST /api/auth/logout            # End session
\`\`\`

### Opportunities (Marketplace)
\`\`\`
POST /api/leads                      # Create opportunity (buyer)
GET  /api/leads                      # Browse opportunities (vendor)
GET  /api/leads/{id}                 # View opportunity details
PUT  /api/leads/{id}                 # Update opportunity (buyer)
POST /api/leads/{id}/submit          # Submit for review (buyer)
POST /api/leads/{id}/interest        # Express interest (vendor)
GET  /api/leads/{id}/interests       # View interests (buyer)
POST /api/leads/{id}/accept/{vendor_id}  # Accept vendor (buyer)
\`\`\`

### Vendor Listings
\`\`\`
POST /api/listings                   # Create listing (vendor)
GET  /api/listings                   # Browse listings
GET  /api/listings/{id}              # View listing details
PUT  /api/listings/{id}              # Update listing (vendor)
POST /api/listings/{id}/submit       # Submit for review (vendor)
\`\`\`

### Messages
\`\`\`
GET  /api/messages/conversations     # List conversations
GET  /api/messages/{conversation_id} # Get messages
POST /api/messages/{conversation_id} # Send encrypted message
\`\`\`

### Subscriptions
\`\`\`
GET  /api/subscriptions/plans        # View subscription plans
POST /api/subscriptions/subscribe    # Subscribe to plan
GET  /api/subscriptions/current      # Get current subscription
POST /api/subscriptions/cancel       # Cancel subscription
\`\`\`

### Admin
\`\`\`
GET  /api/admin/leads/pending        # Pending opportunities
POST /api/admin/leads/{id}/approve   # Approve opportunity
POST /api/admin/leads/{id}/reject    # Reject opportunity
GET  /api/admin/vendors/pending      # Pending vendor verifications
POST /api/admin/vendors/{id}/verify  # Verify vendor
POST /api/admin/vendors/{id}/reject  # Reject vendor
GET  /api/admin/users                # List all users
POST /api/admin/users/{id}/suspend   # Suspend user
\`\`\`

## Security Features

1. **PGP Authentication** - No passwords, cryptographic identity only
2. **End-to-End Encryption** - Messages encrypted client-side
3. **Tor Hidden Service** - .onion address for anonymity
4. **Rate Limiting** - Redis-backed with role-based limits
5. **CSRF Protection** - Token-based form protection
6. **Input Validation** - Strict validation on all inputs
7. **SQL Injection Prevention** - Parameterized queries via SQLAlchemy
8. **XSS Prevention** - Jinja2 auto-escaping

## Monero Integration

- **Single-use addresses** - Each transaction gets unique subaddress
- **Payment monitoring** - Celery workers check for confirmations
- **Price oracle** - Multi-source XMR/USD conversion
- **Escrow support** - Funds held until transaction complete

## Deployment

The platform is deployed to a dedicated server with:
- Tor hidden service configuration
- PostgreSQL database
- Redis cache
- Celery workers
- Monero daemon (optional, can use remote node)
- Systemd service management

See DEPLOY_NOW.md for complete deployment instructions.
\`\`\`

## Build Order & Dependencies

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
├── Opportunity submission & management (Buyer)
├── Opportunity browsing for vendors
├── Interest expression & matching
├── Secure messaging system
└── Admin moderation tools

Phase 4: Vendor Listings & Payments (Week 8-10)
├── Listing CRUD operations
├── Tier management
├── Contribution flow
├── Vendor payment integration (Monero)
├── Payment monitoring worker

Phase 5: Subscriptions & Polish (Week 11-12)
├── Vendor subscription system
├── Security audit
├── Performance optimization
├── Error handling & Logging
├── Documentation

Phase 6: Deployment (Week 13)
├── Infrastructure provisioning
├── Tor onion service setup
├── SSL/TLS configuration
├── Backup procedures
└── Launch checklist
## API Endpoints Summary

Authentication
POST /api/auth/register          # Register with PGP key
POST /api/auth/challenge         # Get auth challenge
POST /api/auth/verify            # Verify signed challenge
POST /api/auth/logout            # End session
GET  /api/auth/session             # Validate session

Opportunities (Marketplace)
POST /api/leads                      # Create opportunity (buyer)
GET  /api/leads                      # Browse opportunities (vendor)
GET  /api/leads/{id}                 # View opportunity details
PUT  /api/leads/{id}                 # Update opportunity (buyer)
POST /api/leads/{id}/submit          # Submit for review (buyer)
POST /api/leads/{id}/interest        # Express interest (vendor)
GET  /api/leads/{id}/interests       # View interests (buyer)
POST /api/leads/{id}/accept/{vendor_id}  # Accept vendor (buyer)

Vendor Listings
POST /api/listings                   # Create listing (vendor)
GET  /api/listings                   # Browse listings
GET  /api/listings/{id}              # View listing details
PUT  /api/listings/{id}              # Update listing (vendor)
POST /api/listings/{id}/submit       # Submit for review (vendor)

Messages
GET  /api/messages/conversations     # List conversations
GET  /api/messages/{conversation_id} # Get messages
POST /api/messages/{conversation_id} # Send encrypted message

Subscriptions
GET  /api/subscriptions/plans        # View subscription plans
POST /api/subscriptions/subscribe    # Subscribe to plan
GET  /api/subscriptions/current      # Get current subscription
POST /api/subscriptions/cancel       # Cancel subscription

Admin
GET  /api/admin/leads/pending        # Pending opportunities
POST /api/admin/leads/{id}/approve   # Approve opportunity
POST /api/admin/leads/{id}/reject    # Reject opportunity
GET  /api/admin/vendors/pending      # Pending vendor verifications
POST /api/admin/vendors/{id}/verify  # Verify vendor
POST /api/admin/vendors/{id}/reject  # Reject vendor
GET  /api/admin/users                # List all users
POST /api/admin/users/{id}/suspend   # Suspend user

## Security Features

1. **PGP Authentication** - No passwords, cryptographic identity only
2. **End-to-End Encryption** - Messages encrypted client-side
3. **Tor Hidden Service** - .onion address for anonymity
4. **Rate Limiting** - Redis-backed with role-based limits
5. **CSRF Protection** - Token-based form protection
6. **Input Validation** - Strict validation on all inputs
7. **SQL Injection Prevention** - Parameterized queries via SQLAlchemy
8. **XSS Prevention** - Jinja2 auto-escaping

## Monero Integration

- **Single-use addresses** - Each transaction gets unique subaddress
- **Payment monitoring** - Celery workers check for confirmations
- **Price oracle** - Multi-source XMR/USD conversion
- **Escrow support** - Funds held until transaction complete

## Deployment

The platform is deployed to a dedicated server with:
- Tor hidden service configuration
- PostgreSQL database
- Redis cache
- Celery workers
- Monero daemon (optional, can use remote node)
- Systemd service management

See DEPLOY_NOW.md for complete deployment instructions.
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

# Add VendorProfile and BuyerProfile for the new marketplace model
from app.models.user import VendorProfile, BuyerProfile


__all__ = [
    "User",
    "UserRole",
    "JournalistProfile",
    "SourceProfile",
    "VerificationStatus",
    "AuthChallenge",
    "Session",
    "VendorProfile", # Added
    "BuyerProfile",  # Added
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
from sqlalchemy import String, Text, Boolean, Integer, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    BUYER = "buyer"      # New role for marketplace
    VENDOR = "vendor"    # New role for marketplace
    ADMIN = "admin"
    # SOURCE = "source"  # Removed
    # JOURNALIST = "journalist" # Removed


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
    vendor_profile: Mapped[Optional["VendorProfile"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
    buyer_profile: Mapped[Optional["BuyerProfile"]] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
    sessions: Mapped[List["Session"]] = relationship(back_populates="user")
    
    # For Admin view: link to verifier user if applicable
    verified_by_user: Mapped[Optional["User"]] = relationship(lazy="selectin") # For linking admin verifier
    
    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role.value})>"


class VendorProfile(Base):
    """Extended profile for vendor users."""
    
    __tablename__ = "vendor_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    shop_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)), nullable=True)
    
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SQLEnum(VerificationStatus), default=VerificationStatus.PENDING
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True) # Admin who verified
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Subscription info
    subscription_tier: Mapped[str] = mapped_column(String(20), default="free") # e.g., "free", "basic", "pro"
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    total_sales: Mapped[int] = mapped_column(Integer, default=0) # Count of successful transactions
    rating: Mapped[float] = mapped_column(Float, default=0.0) # Average rating from buyers
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="vendor_profile")
    verifier: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[verified_by]) # Link to admin user


class BuyerProfile(Base):
    """Extended profile for buyer users."""
    
    __tablename__ = "buyer_profiles"
    
    id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    
    anonymous_alias: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    trust_score: Mapped[int] = mapped_column(Integer, default=50) # Calculated trust score
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="buyer_profile")


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
from app.models.user import UserRole # Import necessary roles


class LeadStatus(str, enum.Enum):
    # Roles relevant to opportunities/listings
    DRAFT = "draft"           # For buyers creating opportunities
    SUBMITTED = "submitted"     # Buyer submitted opportunity for review
    PUBLISHED = "published"     # Opportunity is live for vendors
    MATCHED = "matched"         # Buyer accepted a vendor's interest
    IN_PROGRESS = "in_progress" # Transaction between buyer and vendor
    COMPLETED = "completed"     # Transaction finished successfully
    FAILED = "failed"           # Transaction failed
    WITHDRAWN = "withdrawn"     # Opportunity or vendor interest withdrawn
    EXPIRED = "expired"         # Opportunity/listing expired


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
    """Buyer opportunity requests."""
    
    __tablename__ = "opportunities" # Renamed from 'leads' to 'opportunities'
    
    buyer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Public information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[LeadCategory] = mapped_column(SQLEnum(LeadCategory), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False) # Renamed from 'summary'
    requirements: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)), nullable=True) # Renamed from 'evidence_types'
    geographic_scope: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    budget_usd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Added budget field
    
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
    accepted_vendor_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Completion
    completion_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Notes from buyer/vendor
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    interests: Mapped[List["OpportunityInterest"]] = relationship(back_populates="opportunity")
    
    # Added relationships for admin view
    reviewer: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[reviewed_by])
    buyer: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[buyer_id])
    vendor: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[accepted_vendor_id])


class OpportunityInterest(Base):
    """Vendor interest in buyer opportunities."""
    
    __tablename__ = "opportunity_interests"
    
    opportunity_id: Mapped[UUID] = mapped_column(ForeignKey("opportunities.id"), nullable=False) # Updated FK
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    pitch: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InterestStatus] = mapped_column(
        SQLEnum(InterestStatus), default=InterestStatus.PENDING
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    opportunity: Mapped["Lead"] = relationship(back_populates="interests") # Updated relationship name
    vendor: Mapped["User"] = relationship(lazy="selectin") # Link to vendor user


# ============================================================================
# FILE: app/models/message.py
# ============================================================================
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List
from uuid import UUID
import enum

from app.database import Base
from app.models.user import User # Import User for sender/recipient


class Conversation(Base):
    """Secure conversation between buyer and vendor."""
    
    __tablename__ = "conversations"
    
    opportunity_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("opportunities.id"), nullable=True # Updated FK
    )
    buyer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    last_message_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    closed_by: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation")
    
    # Added relationships for easier access
    buyer: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[buyer_id])
    vendor: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[vendor_id])
    opportunity: Mapped["Lead"] = relationship(lazy="selectin") # Updated relationship name


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
    sender: Mapped["User"] = relationship(lazy="selectin") # Link to sender user


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
from app.models.user import User # For relationships
from app.models.payment import Deposit # For contributions


class ListingStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    PAUSED = "paused"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class ListingCategory(str, enum.Enum):
    # Changed categories to be more marketplace-oriented
    DIGITAL_GOODS = "digital_goods"
    PHYSICAL_GOODS = "physical_goods"
    SERVICES = "services"
    CONSULTING = "consulting"
    SOFTWARE_DEV = "software_dev"
    SECURE_INFRASTRUCTURE = "secure_infrastructure"
    RESEARCH_INVESTIGATION = "research_investigation"
    GENERAL_SUPPORT = "general_support" # Keep for general needs


class ContributionStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SupportListing(Base):
    """Vendor listings for services/goods."""
    
    __tablename__ = "vendor_listings" # Renamed from 'support_listings'
    
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Public information
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    category: Mapped[ListingCategory] = mapped_column(
        SQLEnum(ListingCategory), nullable=False
    )
    headline: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False) # Renamed from 'story'
    
    disclosure_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Goals/Pricing (for vendors)
    price_usd_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Fixed price or base for tiers
    # funding_goal_usd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Removed, replaced by tiers/fixed price
    # funding_deadline: Mapped[Optional[datetime]] = mapped_column(nullable=True) # Removed, replaced by subscription/fixed price
    
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
    total_raised_atomic: Mapped[int] = mapped_column(BigInteger, default=0) # Total XMR value from transactions
    supporter_count: Mapped[int] = mapped_column(Integer, default=0) # Count of transactions/buyers
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    closes_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    tiers: Mapped[List["VendorTier"]] = relationship(back_populates="listing") # Renamed from SupportTier
    transactions: Mapped[List["Transaction"]] = relationship( # Renamed from SupportContribution
        back_populates="listing"
    )
    reviews: Mapped[List["Review"]] = relationship(back_populates="listing") # Added Reviews
    updates: Mapped[List["ListingUpdate"]] = relationship(back_populates="listing")
    
    # Added relationships for admin view
    verifier: Mapped["User"] = relationship(lazy="selectin", foreign_keys=[verified_by])


class VendorTier(Base):
    """Configurable tiers for vendor services/goods."""
    
    __tablename__ = "vendor_tiers"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("vendor_listings.id"), nullable=False # Updated FK
    )
    
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount_usd: Mapped[int] = mapped_column(Integer, nullable=False)  # Cents
    
    perks: Mapped[Optional[List]] = mapped_column(JSONB, default=list)
    is_highlighted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    max_purchasers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # Renamed from max_supporters
    current_purchasers: Mapped[int] = mapped_column(Integer, default=0) # Renamed from current_supporters
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="tiers") # Updated relationship name
    
    @property
    def is_available(self) -> bool:
        if not self.max_purchasers:
            return True
        return self.current_purchasers < self.max_purchasers
    
    @property
    def spots_remaining(self) -> Optional[int]:
        if not self.max_purchasers:
            return None
        return self.max_purchasers - self.current_purchasers


class Transaction(Base):
    """Individual transaction for a vendor listing."""
    
    __tablename__ = "transactions"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("vendor_listings.id"), nullable=False # Updated FK
    )
    tier_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("vendor_tiers.id"), nullable=True # Updated FK
    )
    
    # Buyer info
    buyer_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    buyer_alias: Mapped[Optional[str]] = mapped_column(String(64), nullable=True) # Alias if buyer is anonymous
    is_anonymous_buyer: Mapped[bool] = mapped_column(Boolean, default=True) # Track buyer anonymity preference
    
    # Vendor info (for context)
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Payment
    amount_usd_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_xmr_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exchange_rate_used: Mapped[str] = mapped_column(String(20), nullable=False)
    
    deposit_id: Mapped[UUID] = mapped_column(ForeignKey("deposits.id"), nullable=False)
    
    # Message (optional)
    encrypted_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Status
    status: Mapped[ContributionStatus] = mapped_column( # Reusing ContributionStatus enum
        SQLEnum(ContributionStatus), default=ContributionStatus.PENDING
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    tx_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tx_confirmations: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="transactions") # Updated relationship name
    tier: Mapped["VendorTier"] = relationship(lazy="selectin") # Updated relationship name
    deposit: Mapped["Deposit"] = relationship(lazy="selectin") # Link to deposit


class Review(Base):
    """Reviews left by buyers for vendors."""
    
    __tablename__ = "reviews"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("vendor_listings.id"), nullable=False # Updated FK
    )
    transaction_id: Mapped[UUID] = mapped_column(
        ForeignKey("transactions.id"), unique=True, nullable=False # Updated FK
    )
    
    # Reviewer info
    reviewer_user_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewer_alias: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    rating: Mapped[int] = mapped_column(Integer, nullable=False) # 1-5 stars
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="reviews") # Updated relationship name
    transaction: Mapped["Transaction"] = relationship(lazy="selectin") # Updated relationship name


class ListingUpdate(Base):
    """Progress updates from vendors."""
    
    __tablename__ = "listing_updates"
    
    listing_id: Mapped[UUID] = mapped_column(
        ForeignKey("vendor_listings.id"), nullable=False # Updated FK
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    minimum_tier_amount: Mapped[int] = mapped_column(Integer, default=0) # Minimum tier to see this update
    
    media_ids: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(36)), nullable=True) # References to uploaded media
    
    # Relationships
    listing: Mapped["SupportListing"] = relationship(back_populates="updates") # Updated relationship name


# ============================================================================
# FILE: app/models/payment.py
# ============================================================================
from sqlalchemy import String, Text, Integer, BigInteger, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from uuid import UUID
import enum

from app.database import Base
from app.models.user import User # For relationships


class DepositStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    FAILED = "failed"


class DepositPurpose(str, enum.Enum):
    SUBSCRIPTION = "subscription"
    SUPPORT_CONTRIBUTION = "support_contribution" # Changed from SUPPORT_CONTRIBUTION
    TRANSACTION = "transaction"              # For marketplace transactions
    TOP_UP = "top_up"
    ORDER = "order"
    VENDOR_UPGRADE = "vendor_upgrade"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    BASIC = "basic"      # Renamed from FREELANCER
    PRO = "pro"          # Renamed from OUTLET
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
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # e.g., "sub:<user_id>:<tier>" or "tx:<transaction_id>"
    
    status: Mapped[DepositStatus] = mapped_column(
        SQLEnum(DepositStatus), default=DepositStatus.PENDING
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    tx_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confirmations: Mapped[int] = mapped_column(Integer, default=0)
    
    qr_code_base64: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Subscription(Base):
    """Vendor/User subscription management."""
    
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
    
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False) # e.g., "monero", "stripe"
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # e.g., Deposit ID or Stripe Charge ID
    
    # Relationships
    user: Mapped["User"] = relationship(lazy="selectin")


# ============================================================================
# FILE: app/schemas/auth.py
# ============================================================================
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class RegisterRequest(BaseModel):
    """Registration initiation request."""
    
    username: str = Field(..., min_length=3, max_length=32)
    role: str = Field(..., pattern="^(buyer|vendor)$") # Updated roles
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
        if not v.strip().startswith("-----BEGIN PGP PUBLIC KEY BLOCK-----"):
            raise ValueError("Invalid PGP public key format: must start with BEGIN PGP PUBLIC KEY BLOCK")
        if not v.strip().endswith("-----END PGP PUBLIC KEY BLOCK-----"):
            raise ValueError("Invalid PGP public key format: must end with END PGP PUBLIC KEY BLOCK")
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
    """Opportunity creation request."""
    
    title: str = Field(..., min_length=10, max_length=200)
    category: str = Field(...)
    subcategory: Optional[str] = Field(default=None, max_length=100)
    description: str = Field(..., min_length=200, max_length=2000) # Renamed from summary
    requirements: List[str] = Field(..., min_length=1) # Renamed from evidence_types
    geographic_scope: Optional[List[str]] = Field(default=None)
    budget_usd: Optional[int] = Field(default=None, ge=500) # Minimum budget $5
    time_sensitivity: Optional[str] = Field(
        default=None, pattern="^(urgent|moderate|archival)$"
    )
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        # Check for PII patterns (basic)
        import re
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+.[a-zA-Z]{2,}"
        phone_pattern = r"\+?\d{1,3}?[-.\s]?$$?\d{1,4}?$$?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
        
        if re.search(email_pattern, v):
            raise ValueError("Please do not include email addresses in the description")
        if re.search(phone_pattern, v):
            raise ValueError("Please do not include phone numbers in the description")
        
        return v


class LeadResponse(BaseModel):
    """Opportunity response model."""
    
    id: str
    title: str
    category: str
    subcategory: Optional[str]
    description: str
    requirements: List[str]
    geographic_scope: Optional[List[str]]
    budget_usd: Optional[int]
    time_sensitivity: Optional[str]
    status: str
    submitted_at: Optional[str]
    created_at: str
    
    # Vendor matching info (for vendors viewing opportunities)
    vendor_interest_status: Optional[str] = None # e.g., "applied", "accepted"
    accepted_vendor_username: Optional[str] = None
    accepted_vendor_alias: Optional[str] = None # If vendor uses an alias
    accepted_vendor_shop_name: Optional[str] = None


class LeadListResponse(BaseModel):
    """Paginated opportunity list response."""
    
    opportunities: List[LeadResponse] # Renamed from leads
    total: int
    page: int
    page_size: int
    total_pages: int


class LeadInterestRequest(BaseModel):
    """Vendor interest expression."""
    
    pitch: str = Field(..., min_length=50, max_length=1000)
    # Add fields for vendor profile context if needed, e.g., shop_name, categories


class LeadInterestResponse(BaseModel):
    """Interest response for buyers."""
    
    interest_id: str
    vendor_username: str
    vendor_shop_name: Optional[str]
    vendor_categories: Optional[List[str]]
    vendor_rating: float
    pitch: str
    status: str
    created_at: str


# ============================================================================
# FILE: app/schemas/listing.py
# ============================================================================
from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.models.listing import ListingStatus, ListingCategory, ContributionStatus # Import necessary enums


class TierCreateRequest(BaseModel):
    """Tier creation request for vendor listings."""
    
    name: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=20, max_length=500)
    amount_usd: int = Field(..., ge=100)  # Minimum $1 (100 cents)
    perks: Optional[List[str]] = Field(default=None)
    is_highlighted: bool = Field(default=False)
    max_purchasers: Optional[int] = Field(default=None, ge=1) # Renamed from max_supporters


class ListingResponse(BaseModel):
    """Vendor listing response model."""
    
    id: str
    slug: str
    title: str
    category: str
    headline: str
    description: str # Renamed from story
    disclosure_summary: Optional[str]
    risk_description: Optional[str]
    price_usd_cents: Optional[int] # Added fixed price
    price_usd_display: Optional[str]
    verified: bool
    status: str
    created_at: str
    published_at: Optional[str]
    
    vendor_username: str
    vendor_shop_name: Optional[str]
    vendor_rating: float


class TierResponse(BaseModel):
    """Tier response model for vendor listings."""
    
    id: str
    name: str
    description: str
    amount_usd: int
    amount_display: str
    perks: List[str]
    is_highlighted: bool
    purchasers_remaining: Optional[int] # Renamed from spots_remaining
    is_available: bool


class ContributionCreateRequest(BaseModel):
    """Transaction initiation request."""
    
    tier_id: Optional[str] = Field(default=None) # Specify which tier is being purchased
    buyer_alias: Optional[str] = Field(default=None, max_length=64)
    is_anonymous_buyer: bool = Field(default=True)
    message: Optional[str] = Field(default=None, max_length=1000) # Optional message to vendor


class ContributionResponse(BaseModel):
    """Transaction payment details."""
    
    transaction_id: str
    listing_title: str
    vendor_shop_name: str
    tier_name: Optional[str]
    amount_usd: str
    amount_xmr: str
    xmr_address: str
    payment_id: str
    qr_code_base64: Optional[str]
    expires_at: str
    exchange_rate: str
    status: str


class ReviewResponse(BaseModel):
    """Review response model."""
    
    id: str
    listing_id: str
    transaction_id: str
    reviewer_alias: Optional[str]
    rating: int
    comment: Optional[str]
    is_anonymous: bool
    created_at: str


class ListingUpdateResponse(BaseModel):
    """Listing update response model."""
    id: str
    listing_id: str
    title: str
    content: str
    minimum_tier_amount: int
    media_ids: Optional[List[str]]
    created_at: str


class ListingDetailResponse(BaseModel):
    """Full vendor listing detail with tiers, reviews, and updates."""
    
    listing: ListingResponse
    tiers: List[TierResponse]
    reviews: List[ReviewResponse]
    updates: List[ListingUpdateResponse]


# ============================================================================
# FILE: app/schemas/message.py
# ============================================================================
from pydantic import BaseModel, Field
from typing import Optional, List


class ConversationResponse(BaseModel):
    """Conversation summary."""
    
    id: str
    opportunity_id: Optional[str] # Renamed from lead_id
    opportunity_title: Optional[str] # Renamed from lead_title
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
    sender_id: str
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
    User, UserRole, JournalistProfile, SourceProfile, VendorProfile, BuyerProfile, # Added Vendor/Buyer profiles
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
        
        fingerprint, pgp_key, role_str = pending_data.decode().split("x00", 2)
        
        # Create user
        user = User(
            username=username,
            role=UserRole(role_str),
            pgp_fingerprint=fingerprint,
            pgp_public_key=pgp_key,
        )
        self.db.add(user)
        await self.db.flush()
        
        # Create role-specific profile
        if role_str == "vendor":
            profile = VendorProfile(id=user.id)
            self.db.add(profile)
        elif role_str == "buyer":
            alias = await self._generate_anonymous_alias()
            profile = BuyerProfile(id=user.id, anonymous_alias=alias)
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
        """Generate unique anonymous alias for buyers."""
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
                select(BuyerProfile).where(BuyerProfile.anonymous_alias == alias)
            )
            if not result.scalar_one_or_none():
                return alias
        
        # Fallback with more entropy
        return f"Buyer{secrets.token_hex(6)}"


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
from app.models.listing import Transaction # Import for contribution confirmation


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
api_router.include_router(leads.router, prefix="/opportunities", tags=["Opportunities"]) # Updated prefix
api_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_router.include_router(listings.router, prefix="/listings", tags=["Vendor Listings"]) # Updated tag
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
    SessionInfo,
)


router = APIRouter()


@router.post("/register", response_model=RegisterChallengeResponse)
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


@router.post("/challenge", response_model=RegisterChallengeResponse)
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


@router.post("/verify", response_model=AuthResponse)
async def complete_verification(
    request: ChallengeResponseRequest,
    http_request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    ARCHITECT Protocol Step 2: Submit decrypted challenge to complete action
    (registration or login).
    """
    service = AuthService(db, redis)
    
    # Extract Tor circuit hash if available
    circuit_hash = http_request.headers.get("X-Tor-Circuit-Hash")
    
    # Determine if this is a registration completion or login completion
    # We can check if a pending registration exists in Redis
    is_registration = await redis.exists(f"pending_reg:{request.username.lower()}")
    
    try:
        if is_registration:
            result = await service.complete_registration(
                request.username,
                request.challenge_response,
            )
        else:
            result = await service.complete_login(
                request.username,
                request.challenge_response,
                circuit_hash,
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
    
    return {"success": True, "message": "Logged out successfully"}


@router.get("/session", response_model=SessionInfo)
async def get_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Validate the current session and return user info.
    """
    token = request.cookies.get("vault_session")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    service = AuthService(db, redis)
    user = await service.validate_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session token")
    
    return SessionInfo(
        user_id=str(user.id),
        username=user.username,
        role=user.role.value,
        expires_at=user.sessions[0].expires_at.isoformat(), # Assuming one active session per user for this check
    )


# ============================================================================
# FILE: app/api/leads.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.models.lead import Lead, LeadStatus, LeadCategory, EvidenceType, LeadInterest, InterestStatus # Updated models
from app.services.auth_service import AuthService
from app.dependencies import get_current_user
from app.schemas.lead import (
    LeadCreateRequest, LeadResponse, LeadListResponse, # Using LeadResponse for Opportunities
    LeadInterestRequest, LeadInterestResponse
)
from app.services.lead_service import LeadService, LeadError


router = APIRouter()


async def get_lead_service(db: AsyncSession = Depends(get_db)) -> LeadService:
    return LeadService(db)


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_opportunity( # Renamed from create_lead
    request: LeadCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Submit a new opportunity as a buyer.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Only buyers can submit opportunities")
    
    try:
        opportunity = await lead_service.create_opportunity(current_user.id, request) # Updated method name
        return lead_service.model_to_response(opportunity) # Updated model conversion
    except LeadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/", response_model=LeadListResponse)
async def list_opportunities( # Renamed from list_leads
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user), # Make optional for public browsing
    lead_service: LeadService = Depends(get_lead_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
    category: Optional[LeadCategory] = Query(None),
    status: Optional[LeadStatus] = Query(None),
):
    """
    Browse opportunities.
    - Buyers can see their own opportunities (draft/submitted).
    - Vendors can see published opportunities.
    - Admins can see all.
    """
    if current_user and current_user.role == UserRole.BUYER:
        # Buyers can only see their own opportunities
        opportunities, total = await lead_service.get_opportunities_for_buyer( # Updated method name
            buyer_id=current_user.id,
            page=page,
            page_size=page_size,
            category=category,
            status=status,
        )
    elif current_user and current_user.role == UserRole.VENDOR:
        # Vendors can see published opportunities, and those they've expressed interest in
        opportunities, total = await lead_service.get_opportunities_for_vendor( # Updated method name
            vendor_id=current_user.id,
            page=page,
            page_size=page_size,
            category=category,
            status=status,
        )
    elif current_user and current_user.role == UserRole.ADMIN:
        # Admins can see all opportunities
        opportunities, total = await lead_service.get_all_opportunities( # New method for admins
            page=page,
            page_size=page_size,
            category=category,
            status=status,
        )
    else:
        # Public view: only published opportunities
        opportunities, total = await lead_service.get_opportunities_for_vendor( # Reuse vendor method for public view
            page=page,
            page_size=page_size,
            category=category,
            status=LeadStatus.PUBLISHED, # Only published are public
        )
    
    total_pages = (total + page_size - 1) // page_size
    
    return LeadListResponse(
        opportunities=[lead_service.model_to_response(opp) for opp in opportunities], # Updated model conversion
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{opportunity_id}", response_model=LeadResponse)
async def get_opportunity_details( # Renamed from get_lead_detail
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user), # Make optional for public view
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Get detailed information for a specific opportunity.
    Access depends on user role and ownership.
    """
    try:
        opportunity = await lead_service.get_opportunity(opportunity_id) # Updated method name
        
        # Check permissions
        if current_user:
            if current_user.role == UserRole.BUYER:
                if opportunity.buyer_id != current_user.id:
                    raise LeadError("Opportunity not found", status_code=404)
            elif current_user.role == UserRole.VENDOR:
                # Vendors can see published opportunities or ones they've expressed interest in
                if opportunity.status not in [LeadStatus.PUBLISHED, LeadStatus.MATCHED, LeadStatus.IN_PROGRESS]:
                     raise LeadError("Opportunity not found", status_code=404)
                
                interest = await lead_service.get_interest_by_opportunity_and_vendor(opportunity_id, current_user.id)
                if not interest and opportunity.accepted_vendor_id != current_user.id:
                    raise LeadError("Opportunity not found", status_code=404)
            elif current_user.role == UserRole.ADMIN:
                pass # Admins can see everything
        else:
            # Public view: only published opportunities
            if opportunity.status != LeadStatus.PUBLISHED:
                 raise LeadError("Opportunity not found", status_code=404)
        
        return lead_service.model_to_response(opportunity)
    except LeadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{opportunity_id}", response_model=LeadResponse)
async def update_opportunity( # Renamed from update_lead
    opportunity_id: str,
    request: LeadCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Update an opportunity owned by the current buyer.
    Only draft opportunities can be updated.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Only buyers can update opportunities")
    
    try:
        opportunity = await lead_service.update_opportunity(current_user.id, opportunity_id, request) # Updated method name
        return lead_service.model_to_response(opportunity)
    except LeadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{opportunity_id}/submit", response_model=LeadResponse)
async def submit_opportunity_for_review( # Renamed from submit_lead_for_review
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Buyer submits an opportunity for admin review.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Only buyers can submit opportunities")
    
    try:
        opportunity = await lead_service.submit_opportunity(current_user.id, opportunity_id) # Updated method name
        return lead_service.model_to_response(opportunity)
    except LeadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{opportunity_id}/interest", response_model=LeadInterestResponse)
async def express_interest_in_opportunity( # Renamed from express_interest_in_lead
    opportunity_id: str,
    request: LeadInterestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Vendor expresses interest in an opportunity.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can express interest")
    
    try:
        interest = await lead_service.express_interest(current_user.id, opportunity_id, request) # Updated method name
        return lead_service.interest_model_to_response(interest)
    except LeadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{opportunity_id}/interests", response_model=List[LeadInterestResponse])
async def get_opportunity_interests( # Renamed from get_lead_interests
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lead_service: LeadService = Depends(get_lead_service),
):
    """
    Buyer views vendors who have expressed interest in their opportunity.
    """
    if current_user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Only buyers can view opportunity interests")
    
    try:
        opportunity = await lead_service.get_opportunity(opportunity_id) # Updated method name
        if opportunity.buyer_id != current_user.id:
            raise LeadError("Opportunity not found", status_code=404)
        
        interests = await lead_service.get_interests_for_opportunity(opportunity_id) # Updated method name
        return [lead_service.interest_model_to_response(i) for i in interests]
    except LeadError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ============================================================================
# FILE: app/api/messages.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, asc
from typing import List, Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.models.message import Conversation, Message
from app.services.auth_service import AuthService
from app.services.message_service import MessageService, MessageError
from app.services.pgp_service import pgp_service
from app.dependencies import get_current_user
from app.schemas.message import (
    ConversationResponse, MessageCreateRequest, MessageResponse,
    ConversationDetailResponse
)


async def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    return MessageService(db)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
):
    """
    List all conversations for the current user (buyer or vendor).
    """
    conversations, total = await message_service.get_conversations_for_user(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    
    # Fetch related data (opportunity title, other party username/role)
    opportunity_titles = {}
    opportunity_ids = [c.opportunity_id for c in conversations if c.opportunity_id]
    if opportunity_ids:
        from app.models.lead import Lead # Import locally
        stmt = select(Lead.id, Lead.title).where(Lead.id.in_(opportunity_ids))
        result = await db.execute(stmt)
        opportunity_titles = dict(result.fetchall())
    
    other_party_details = {}
    user_ids = [c.buyer_id if c.buyer_id != current_user.id else c.vendor_id for c in conversations]
    if user_ids:
        from app.models.user import User # Import locally
        stmt = select(User.id, User.username, User.role).where(User.id.in_(user_ids))
        result = await db.execute(stmt)
        other_party_details = {row.id: {"username": row.username, "role": row.role.value} for row in result}

    # Update conversation models with fetched data before converting to response
    for conv in conversations:
        if conv.opportunity_id:
            setattr(conv, 'opportunity_title', opportunity_titles.get(str(conv.opportunity_id)))
        
        other_party_id = conv.buyer_id if conv.buyer_id != current_user.id else conv.vendor_id
        if other_party_id in other_party_details:
            details = other_party_details[other_party_id]
            # Attach details to conversation object for response conversion
            # This is a bit of a hack; ideally, query should join directly or use relationship loading
            if conv.buyer_id == current_user.id: # Current user is buyer
                 setattr(conv, 'vendor', type('obj', (object,), {'username': details['username'], 'role': UserRole(details['role'])}))
            else: # Current user is vendor
                 setattr(conv, 'buyer', type('obj', (object,), {'username': details['username'], 'role': UserRole(details['role'])}))

    return [
        message_service.conversation_to_response(c, current_user.id) # Pass only user ID, response converter handles details
        for c in conversations
    ]


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Get full conversation history and recipient PGP details.
    """
    try:
        conversation = await message_service.get_conversation_by_id(conversation_id)
        
        # Authorization check
        if not (conversation.buyer_id == current_user.id or conversation.vendor_id == current_user.id):
            raise MessageError("Conversation not found", status_code=404)
        
        # Mark messages as read
        await message_service.mark_messages_as_read(conversation_id, current_user.id)
        
        # Get recipient info
        recipient_id = conversation.buyer_id if conversation.vendor_id == current_user.id else conversation.vendor_id
        
        # Fetch recipient user details (PGP fingerprint, public key)
        stmt = select(User.pgp_fingerprint, User.pgp_public_key).where(User.id == recipient_id)
        result = await db.execute(stmt)
        recipient_pgp = result.first()
        
        if not recipient_pgp:
            raise MessageError("Recipient not found", status_code=404)
        
        # Fetch messages
        messages = await message_service.get_messages_for_conversation(conversation_id)
        
        # Fetch opportunity title for context
        opportunity_title = None
        if conversation.opportunity_id:
            from app.models.lead import Lead # Import locally
            stmt = select(Lead.title).where(Lead.id == conversation.opportunity_id)
            result = await db.execute(stmt)
            opportunity_title_row = result.first()
            if opportunity_title_row:
                opportunity_title = opportunity_title_row[0]
        
        # Get common conversation info
        conversation_resp = message_service.conversation_to_response(
            conversation, current_user.id, opportunity_title # Pass opportunity title
        )
        
        return ConversationDetailResponse(
            conversation=conversation_resp,
            messages=[message_service.message_to_response(m, current_user.id) for m in messages],
            recipient_pgp_fingerprint=recipient_pgp[0],
            recipient_pgp_public_key=recipient_pgp[1],
        )
    except MessageError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    conversation_id: str,
    request: MessageCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service),
):
    """
    Send an encrypted message within a conversation.
    """
    try:
        # Basic validation of encrypted content structure and hash
        if not request.encrypted_content.startswith("-----BEGIN PGP MESSAGE-----"):
            raise MessageError("Invalid message format", status_code=422)
        
        message = await message_service.send_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            encrypted_content=request.encrypted_content,
            content_hash=request.content_hash,
        )
        return message_service.message_to_response(message, current_user.id)
    except MessageError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ============================================================================
# FILE: app/api/listings.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, asc, literal_column
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.database import get_db
from app.models.user import User, UserRole
from app.models.listing import (
    SupportListing, ListingStatus, ListingCategory, SupportTier, # Renamed to VendorListing, VendorTier
    SupportContribution, ContributionStatus, Review, ListingUpdate # Renamed Transaction, added Review
)
from app.models.listing import VendorListing, VendorTier, Transaction, Review, ListingUpdate # Import new models
from app.services.listing_service import ListingService, ListingError
from app.services.monero_service import MoneroService, MoneroRPCError, monero_service
from app.services.price_oracle import PriceOracleError, price_oracle
from app.dependencies import get_current_user
from app.schemas.listing import (
    ListingCreateRequest, ListingResponse, TierCreateRequest,
    TierResponse, ContributionCreateRequest, ContributionResponse,
    ReviewResponse, ListingUpdateResponse, ListingDetailResponse # Added ReviewResponse, ListingUpdateResponse
)
from app.models.payment import DepositPurpose # For transaction purpose


async def get_listing_service(db: AsyncSession = Depends(get_db)) -> ListingService:
    return ListingService(db)


@router.post("/", response_model=ListingResponse, status_code=201)
async def create_vendor_listing( # Renamed from create_listing
    request: ListingCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Create a new vendor listing.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can create listings")
    
    try:
        listing = await listing_service.create_vendor_listing(current_user.id, request) # Updated method name
        return listing_service.model_to_response(listing)
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/", response_model=List[ListingResponse])
async def list_vendor_listings( # Renamed from list_listings
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
    category: Optional[ListingCategory] = Query(None),
    status: Optional[ListingStatus] = Query(None),
):
    """
    Browse vendor listings.
    - Vendors can see their own listings (draft, pending, active).
    - Buyers can see active, verified listings.
    - Admins can see all.
    """
    if current_user and current_user.role == UserRole.VENDOR:
        listings, total = await listing_service.get_listings_for_vendor( # Updated method name
            vendor_id=current_user.id,
            page=page,
            page_size=page_size,
            category=category,
            status=status,
        )
    elif current_user and current_user.role == UserRole.BUYER:
        # Buyers see active and verified listings
        listings, total = await listing_service.get_listings(
            page=page,
            page_size=page_size,
            category=category,
            status=ListingStatus.ACTIVE,
            verified_by_admin=True,
        )
    elif current_user and current_user.role == UserRole.ADMIN:
        # Admins see all, with optional filters
        listings, total = await listing_service.get_listings(
            page=page,
            page_size=page_size,
            category=category,
            status=status,
        )
    else:
        # Public view (anonymous users)
        listings, total = await listing_service.get_listings(
            page=page,
            page_size=page_size,
            category=category,
            status=ListingStatus.ACTIVE, # Only active and verified listings public
            verified_by_admin=True,
        )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "listings": [listing_service.model_to_response(listing) for listing in listings],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/{listing_slug}", response_model=ListingDetailResponse)
async def get_vendor_listing_detail( # Renamed from get_listing_detail
    listing_slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Get detailed information for a specific vendor listing.
    """
    try:
        listing = await listing_service.get_listing_by_slug(listing_slug)
        
        # Permission check: only owner or admin can see non-active/non-verified listings
        if not listing.verified_by_admin and listing.status not in [ListingStatus.ACTIVE, ListingStatus.PAUSED]:
            if not current_user or current_user.id != listing.vendor_id:
                raise ListingError("Listing not found", status_code=404)
        
        # Increment view count if not owner and not admin/anonymous
        if current_user and current_user.id != listing.vendor_id and current_user.role != UserRole.ADMIN:
            await listing_service.increment_view_count(listing.id)
        elif not current_user: # Anonymous user
            await listing_service.increment_view_count(listing.id)
            
        tiers = await listing_service.get_tiers_for_listing(listing.id)
        reviews = await listing_service.get_reviews_for_listing(listing.id) # Get reviews
        updates = await listing_service.get_updates_for_listing(listing.id)
        
        return ListingDetailResponse(
            listing=listing_service.model_to_response(listing),
            tiers=[listing_service.tier_to_response(tier) for tier in tiers],
            reviews=[listing_service.review_to_response(r) for r in reviews], # Convert reviews
            updates=[listing_service.update_to_response(u) for u in updates],
        )
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{listing_id}", response_model=ListingResponse)
async def update_vendor_listing( # Renamed from update_listing
    listing_id: str,
    request: ListingCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Update a vendor listing owned by the current vendor.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can update their listings")
    
    try:
        listing = await listing_service.update_vendor_listing(current_user.id, listing_id, request) # Updated method name
        return listing_service.model_to_response(listing)
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{listing_id}/submit", response_model=ListingResponse)
async def submit_vendor_listing_for_review( # Renamed from submit_listing
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Vendor submits a listing for admin review.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can submit listings")
    
    try:
        listing = await listing_service.submit_listing(current_user.id, listing_id)
        return listing_service.model_to_response(listing)
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{listing_id}/tiers", response_model=TierResponse, status_code=201)
async def add_tier_to_vendor_listing( # Renamed from add_tier_to_listing
    listing_id: str,
    request: TierCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Add a new tier to a vendor listing.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can add tiers")
    
    try:
        tier = await listing_service.add_vendor_tier(current_user.id, listing_id, request) # Updated method name
        return listing_service.tier_to_response(tier)
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.put("/{listing_id}/tiers/{tier_id}", response_model=TierResponse)
async def update_vendor_tier( # Renamed from update_tier_for_listing
    listing_id: str,
    tier_id: str,
    request: TierCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Update an existing vendor tier.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can update tiers")
    
    try:
        tier = await listing_service.update_vendor_tier(current_user.id, listing_id, tier_id, request) # Updated method name
        return listing_service.tier_to_response(tier)
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{listing_slug}/purchase", response_model=ContributionResponse, status_code=201) # Renamed from contribute
async def initiate_transaction( # Renamed from initiate_contribution
    listing_slug: str,
    request: ContributionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
    monero_service: MoneroService = Depends(lambda: monero_service),
):
    """
    Initiate a purchase transaction for a vendor listing.
    Generates a Monero deposit address.
    """
    # Get the listing
    try:
        listing = await listing_service.get_listing_by_slug(listing_slug)
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    # Validate buyer role if user is logged in
    if current_user and current_user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Only buyers can initiate transactions")
    
    # Get target tier if specified
    target_tier = None
    if request.tier_id:
        try:
            target_tier = await listing_service.get_vendor_tier_by_id(request.tier_id) # Updated method name
            if not target_tier or target_tier.listing_id != listing.id:
                raise ListingError("Invalid tier specified", status_code=422)
        except ListingError as e:
            raise HTTPException(status_code=e.status_code, detail=e.message)
    
    # Determine amount
    if not target_tier:
        raise ListingError("Please select a vendor tier", status_code=422)
    
    transaction_amount_usd_cents = target_tier.amount_usd
    
    # Get current XMR/USD exchange rate
    try:
        xmr_usd_price = await price_oracle.get_xmr_usd_price()
    except PriceOracleError as e:
        raise ListingError(f"Price oracle unavailable: {e}", status_code=503)
    
    # Calculate XMR amount
    transaction_amount_xmr = Decimal(transaction_amount_usd_cents) / xmr_usd_price
    transaction_amount_atomic = monero_service.xmr_to_atomic(transaction_amount_xmr)
    
    # Create deposit address
    try:
        deposit = await monero_service.create_deposit_address(
            db=db,
            user_id=str(current_user.id) if current_user else None, # Link to buyer user if logged in
            purpose=DepositPurpose.TRANSACTION, # Purpose is now TRANSACTION
            expected_amount_atomic=transaction_amount_atomic,
            reference_id=f"tx:{listing.id}:{target_tier.id}", # Reference includes listing and tier ID
            expires_hours=24, # Addresses expire after 24 hours
        )
    except MoneroRPCError as e:
        raise ListingError(f"Failed to create Monero address: {e}", status_code=503)
    
    # Create transaction record
    try:
        transaction = await listing_service.create_transaction( # Updated method name
            listing_id=listing.id,
            vendor_id=listing.vendor_id, # Add vendor ID for context
            tier_id=target_tier.id,
            buyer_user_id=str(current_user.id) if current_user else None,
            buyer_alias=request.buyer_alias,
            is_anonymous_buyer=request.is_anonymous_buyer,
            encrypted_message=request.message,
            deposit_id=str(deposit.id),
            amount_usd_cents=transaction_amount_usd_cents,
            amount_xmr_atomic=transaction_amount_atomic,
            exchange_rate_used=f"{xmr_usd_price:.8f}" # Store rate for reference
        )
        
        return ContributionResponse( # Reusing ContributionResponse schema
            transaction_id=str(transaction.id),
            listing_title=listing.title,
            vendor_shop_name=listing.vendor.shop_name if listing.vendor and listing.vendor.shop_name else "Unknown Vendor",
            tier_name=target_tier.name,
            amount_usd=f"{Decimal(transaction_amount_usd_cents) / 100.0:.2f}",
            amount_xmr=f"{monero_service.atomic_to_xmr(transaction_amount_atomic):.8f}",
            xmr_address=deposit.address,
            payment_id=deposit.payment_id,
            qr_code_base64=deposit.qr_code_base64,
            expires_at=deposit.expires_at.isoformat(),
            exchange_rate=f"{xmr_usd_price:.8f}",
            status=transaction.status.value,
        )
    except ListingError as e:
        # If transaction creation fails, attempt to clean up the deposit address if possible
        # (This part might be complex depending on Monero RPC capabilities)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        # Catch any unexpected errors during transaction creation
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/{listing_id}/reviews", response_model=List[ReviewResponse])
async def get_listing_reviews( # Renamed from get_listing_supporters
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Get reviews for a vendor listing.
    """
    try:
        reviews = await listing_service.get_reviews_for_listing(listing_id)
        return [listing_service.review_to_response(r) for r in reviews]
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/{listing_id}/updates", response_model=Dict[str, str], status_code=201)
async def add_update_to_listing(
    listing_id: str,
    title: str = Query(..., min_length=5, max_length=200),
    content: str = Query(..., min_length=50, max_length=5000),
    minimum_tier_amount: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    listing_service: ListingService = Depends(get_listing_service),
):
    """
    Add a progress update to a vendor listing.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can add updates")
    
    try:
        update = await listing_service.add_listing_update( # Updated method name
            current_user.id, listing_id, title, content, minimum_tier_amount
        )
        return {"message": "Update added successfully", "update_id": str(update.id)}
    except ListingError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ============================================================================
# FILE: app/api/subscriptions.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.database import get_db
from app.models.user import User, UserRole
from app.models.payment import Subscription, SubscriptionTier, DepositPurpose
from app.services.subscription_service import SubscriptionService, SubscriptionError
from app.services.monero_service import MoneroService, monero_service
from app.services.price_oracle import PriceOracleError, price_oracle
from app.dependencies import get_current_user
from app.schemas.auth import AuthResponse # Reusing AuthResponse for session update
from app.schemas.payment import (
    SubscriptionPlanResponse, SubscriptionCreateRequest,
    SubscriptionResponse, SubscriptionCancelResponse
)
from app.config import settings


async def get_subscription_service(db: AsyncSession = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(db)


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    listing_service: ListingService = Depends(get_listing_service), # Used for fallback pricing if needed
):
    """
    Get available subscription plans for vendors.
    """
    plans = []
    
    # Basic Tier
    plans.append(SubscriptionPlanResponse(
        tier=SubscriptionTier.BASIC.value, # Renamed from Freelancer
        price_usd=settings.PRICE_FREELANCER_MONTHLY / 100.0,
        features=["Basic vendor listing", "Respond to 5 opportunities/month"],
        description="For new vendors and basic services.",
    ))
    
    # Pro Tier
    plans.append(SubscriptionPlanResponse(
        tier=SubscriptionTier.PRO.value, # Renamed from Outlet
        price_usd=settings.PRICE_OUTLET_MONTHLY / 100.0,
        features=["All Basic features", "Priority listing placement", "Unlimited opportunities responses", "Enhanced analytics"],
        description="For established vendors seeking more visibility.",
    ))
    
    # Enterprise Tier
    plans.append(SubscriptionPlanResponse(
        tier=SubscriptionTier.ENTERPRISE.value,
        price_usd=settings.PRICE_ENTERPRISE_MONTHLY / 100.0,
        features=["All Pro features", "Featured vendor status", "Dedicated support channel", "API access"],
        description="For premium vendors and enterprise solutions.",
    ))
    
    return plans


@router.post("/subscribe", response_model=Dict[str, Any], status_code=201) # Changed route to /subscribe
async def subscribe_to_plan(
    request: SubscriptionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    monero_service: MoneroService = Depends(lambda: monero_service),
):
    """
    Start a new subscription or renew an existing one.
    Returns payment details (Monero address) if paying with XMR.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can subscribe")
    
    try:
        # Determine price based on tier
        tier = request.tier
        price_usd_cents = 0
        if tier == SubscriptionTier.BASIC.value:
            price_usd_cents = settings.PRICE_FREELANCER_MONTHLY
        elif tier == SubscriptionTier.PRO.value:
            price_usd_cents = settings.PRICE_OUTLET_MONTHLY
        elif tier == SubscriptionTier.ENTERPRISE.value:
            price_usd_cents = settings.PRICE_ENTERPRISE_MONTHLY
        else:
            raise SubscriptionError("Invalid subscription tier", status_code=422)
        
        # Get current XMR/USD exchange rate
        try:
            xmr_usd_price = await price_oracle.get_xmr_usd_price()
        except PriceOracleError as e:
            raise SubscriptionError(f"Price oracle unavailable: {e}", status_code=503)
        
        # Calculate XMR amount
        price_xmr_atomic = monero_service.xmr_to_atomic(Decimal(price_usd_cents) / xmr_usd_price)
        
        # Create Monero deposit address if paying with XMR
        if request.payment_method == "monero":
            deposit = await monero_service.create_deposit_address(
                db=db,
                user_id=str(current_user.id),
                purpose=DepositPurpose.SUBSCRIPTION,
                expected_amount_atomic=price_xmr_atomic,
                reference_id=f"sub:{current_user.id}:{tier}",
                expires_hours=48, # Longer expiry for subscriptions
            )
            
            # Create pending subscription record
            subscription = await subscription_service.create_subscription(
                user_id=current_user.id,
                tier=tier,
                price_usd_cents=price_usd_cents,
                price_xmr_atomic=price_xmr_atomic,
                payment_method=request.payment_method,
                payment_reference=str(deposit.id), # Store deposit ID as reference
            )
            
            return {
                "subscription_id": str(subscription.id),
                "tier": tier,
                "amount_usd": f"{Decimal(price_usd_cents) / 100.0:.2f}",
                "amount_xmr": f"{monero_service.atomic_to_xmr(price_xmr_atomic):.8f}",
                "xmr_address": deposit.address,
                "payment_id": deposit.payment_id,
                "qr_code_base64": deposit.qr_code_base64,
                "expires_at": deposit.expires_at.isoformat(),
                "exchange_rate": f"{xmr_usd_price:.8f}",
                "status": subscription.status.value,
            }
        elif request.payment_method == "stripe":
            # TODO: Implement Stripe integration
            raise SubscriptionError("Stripe payment not yet implemented", status_code=501)
        else:
            raise SubscriptionError("Invalid payment method", status_code=422)
            
    except (SubscriptionError, MoneroRPCError, PriceOracleError) as e:
        raise HTTPException(status_code=getattr(e, 'status_code', 500), detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Get the current active subscription for the vendor.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can view subscriptions")
    
    try:
        subscription = await subscription_service.get_active_subscription_for_user(current_user.id)
        if not subscription:
            # If no active subscription, return a default 'free' plan representation
            return SubscriptionResponse(
                user_id=str(current_user.id),
                tier=SubscriptionTier.FREE.value,
                price_usd="0.00", # Default to string format
                price_xmr="0.0",
                started_at=None,
                expires_at=None,
                status=SubscriptionStatus.ACTIVE.value, # Free tier is always active
                auto_renew=False,
                payment_method="none",
            )
        
        # Fetch associated deposit details if applicable (for XMR payments)
        deposit_details = None
        if subscription.payment_method == "monero" and subscription.payment_reference:
            from app.models.payment import Deposit
            stmt = select(Deposit).where(Deposit.id == subscription.payment_reference)
            result = await db.execute(stmt)
            deposit = result.scalar_one_or_none()
            if deposit:
                deposit_details = {
                    "address": deposit.address,
                    "expires_at": deposit.expires_at.isoformat(),
                    "status": deposit.status.value,
                    "tx_hash": deposit.tx_hash,
                    "confirmations": deposit.confirmations,
                }
        
        return subscription_service.model_to_response(subscription, deposit_details)
        
    except SubscriptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/cancel", response_model=SubscriptionCancelResponse)
async def cancel_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Cancel the current subscription for the vendor.
    """
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(status_code=403, detail="Only vendors can cancel subscriptions")
    
    try:
        success = await subscription_service.cancel_subscription(current_user.id)
        return SubscriptionCancelResponse(success=success, message="Subscription cancellation requested.")
    except SubscriptionError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ============================================================================
# FILE: app/api/admin.py
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.models.user import User, UserRole, VerificationStatus, VendorProfile # Added VendorProfile
from app.models.lead import Lead, LeadStatus # Renamed Lead to Opportunity
from app.models.listing import VendorListing, ListingStatus # Renamed SupportListing to VendorListing
from app.services.auth_service import AuthService
from app.services.admin_service import AdminService, AdminError
from app.dependencies import get_current_user
from app.schemas.auth import AuthResponse # Reusing for updated user info
from app.schemas.admin import (
    AdminLeadResponse, AdminVendorResponse, AdminListingResponse, # Renamed AdminLeadResponse, AdminJournalistResponse
    UserManagementResponse, UserDetailResponse, AdminReviewResponse
)


async def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db)


@router.get("/opportunities/pending", response_model=List[AdminLeadResponse]) # Changed prefix
async def get_pending_opportunities( # Renamed from get_pending_leads
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
):
    """
    Get a list of opportunities awaiting admin review.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can access this endpoint")
    
    opportunities, total = await admin_service.get_opportunities_by_status( # Updated method name
        status=LeadStatus.SUBMITTED, # Still using LeadStatus enum for now
        page=page,
        page_size=page_size,
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "opportunities": [admin_service.opportunity_to_admin_response(opp) for opp in opportunities], # Updated model conversion
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/opportunities/{opportunity_id}/approve", response_model=AdminReviewResponse) # Changed prefix
async def approve_opportunity( # Renamed from approve_lead
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Approve an opportunity for publication.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can approve opportunities")
    
    try:
        opportunity = await admin_service.review_opportunity(opportunity_id, LeadStatus.PUBLISHED, current_user.id) # Updated method name
        return AdminReviewResponse(message="Opportunity approved successfully", status=opportunity.status.value)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/opportunities/{opportunity_id}/reject", response_model=AdminReviewResponse) # Changed prefix
async def reject_opportunity( # Renamed from reject_lead
    opportunity_id: str,
    review_notes: str = Query(..., min_length=10, max_length=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Reject an opportunity with optional review notes.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can reject opportunities")
    
    try:
        opportunity = await admin_service.review_opportunity(opportunity_id, LeadStatus.WITHDRAWN, current_user.id, review_notes=review_notes) # Updated method name
        return AdminReviewResponse(message="Opportunity rejected successfully", status=opportunity.status.value)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/vendors/pending", response_model=List[AdminVendorResponse]) # Changed prefix, Renamed response model
async def get_pending_vendor_verifications( # Renamed from get_pending_journalist_verifications
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
):
    """
    Get a list of vendors awaiting verification.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can manage verifications")
    
    vendors, total = await admin_service.get_users_by_role_and_verification(
        role=UserRole.VENDOR, # Filter by vendor role
        verification_status=VerificationStatus.PENDING,
        page=page,
        page_size=page_size,
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "vendors": [admin_service.vendor_to_admin_response(v) for v in vendors], # Updated model conversion
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/vendors/{user_id}/verify", response_model=AdminReviewResponse) # Changed prefix
async def verify_vendor( # Renamed from verify_journalist
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Verify a vendor's account.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can verify vendors")
    
    try:
        user = await admin_service.verify_user_verification(user_id, VerificationStatus.VERIFIED, current_user.id)
        return AdminReviewResponse(message="Vendor verified successfully", status=user.vendor_profile.verification_status.value) # Updated profile access
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/vendors/{user_id}/reject", response_model=AdminReviewResponse) # Changed prefix
async def reject_vendor( # Renamed from reject_journalist
    user_id: str,
    review_notes: str = Query(..., min_length=10, max_length=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Reject a vendor's verification request.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can reject vendor applications")
    
    try:
        user = await admin_service.verify_user_verification(user_id, VerificationStatus.REJECTED, current_user.id, review_notes=review_notes)
        return AdminReviewResponse(message="Vendor application rejected", status=user.vendor_profile.verification_status.value) # Updated profile access
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/listings/pending", response_model=List[AdminListingResponse])
async def get_pending_vendor_listings( # Renamed from get_pending_listings
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100),
):
    """
    Get a list of vendor listings awaiting admin review.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can manage listings")
    
    listings, total = await admin_service.get_listings_by_status(
        status=ListingStatus.PENDING_REVIEW,
        page=page,
        page_size=page_size,
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "listings": [admin_service.listing_to_admin_response(listing) for listing in listings],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/listings/{listing_id}/approve", response_model=AdminReviewResponse)
async def approve_vendor_listing( # Renamed from approve_listing
    listing_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Approve a vendor listing for publication.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can approve listings")
    
    try:
        listing = await admin_service.review_listing(listing_id, ListingStatus.ACTIVE, current_user.id)
        return AdminReviewResponse(message="Listing approved successfully", status=listing.status.value)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/users", response_model=UserManagementResponse)
async def manage_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=10, le=200),
    role: Optional[UserRole] = Query(None),
    verification_status: Optional[VerificationStatus] = Query(None),
    search_query: Optional[str] = Query(None, description="Search by username or PGP fingerprint"),
):
    """
    Manage users: view, suspend, unsuspend, update roles.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can manage users")
    
    users, total = await admin_service.get_users(
        page=page,
        page_size=page_size,
        role=role,
        verification_status=verification_status,
        search_query=search_query,
    )
    
    total_pages = (total + page_size - 1) // page_size
    
    return UserManagementResponse(
        users=[admin_service.user_to_management_response(user) for user in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Get detailed information for a specific user.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can view user details")
    
    try:
        user = await admin_service.get_user_by_id(user_id)
        return admin_service.user_to_detail_response(user)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/users/{user_id}/suspend", response_model=UserDetailResponse)
async def suspend_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Suspend a user account.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can suspend users")
    
    try:
        user = await admin_service.update_user_status(user_id, is_active=False)
        return admin_service.user_to_detail_response(user)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/users/{user_id}/unsuspend", response_model=UserDetailResponse)
async def unsuspend_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    Unsuspend a user account.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can unsuspend users")
    
    try:
        user = await admin_service.update_user_status(user_id, is_active=True)
        return admin_service.user_to_detail_response(user)
    except AdminError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# ============================================================================
# FILE: app/main.py
# ============================================================================
import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.api.router import api_router


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Anonymous XMR Marketplace Platform", # Updated description
    debug=settings.DEBUG,
)

# Add CORS middleware (optional, for development or specific use cases)
if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include API router
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized.")
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Closing database connection...")
    await close_db()
    logger.info("Database connection closed.")


@app.get("/")
async def read_root(request: Request):
    """
    Root endpoint - redirect to API docs or a landing page.
    """
    # In a production environment, you might serve an HTML landing page here.
    # For now, we'll redirect to the API docs.
    return RedirectResponse(url="/docs")


# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail} for {request.url}")
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unexpected errors."""
    logger.exception(f"An unexpected error occurred for {request.url}: {exc}")
    raise HTTPException(status_code=500, detail="An internal server error occurred.")


if __name__ == "__main__":
    # Example of running the app directly (for development)
    # In production, use a proper WSGI server like Gunicorn with Uvicorn workers.
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True, # Enable auto-reloading for development
        log_level="info"
    )

# ============================================================================
# FILE: app/dependencies.py
# ============================================================================
from fastapi import Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.database import get_db
from app.redis import get_redis # Assuming redis.py is in the same directory or package
from app.services.auth_service import AuthService
from app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> Optional[User]: # Return Optional User for endpoints that don't require auth
    """
    Dependency to get the current authenticated user based on the session cookie.
    Returns None if no valid session is found.
    """
    session_token = request.cookies.get("vault_session")
    
    if not session_token:
        return None # Not authenticated, return None
    
    auth_service = AuthService(db, redis)
    user = await auth_service.validate_session(session_token)
    
    if not user:
        # If session token is invalid, clear the cookie potentially
        # response = Response()
        # response.delete_cookie("vault_session")
        # In a dependency, we just return None or raise HTTPException if required
        return None # Or raise HTTPException(status_code=401, detail="Invalid session token") if auth is mandatory
    
    return user


# ============================================================================
# FILE: app/redis.py
# ============================================================================
from redis.asyncio import Redis
from functools import lru_cache

from app.config import settings


@lru_cache
def get_redis_connection() -> Redis:
    """
    Get a Redis client instance.
    """
    return Redis.from_url(settings.REDIS_URL)


def get_redis() -> Redis:
    """
    Dependency to get a Redis client.
    """
    return get_redis_connection()


# ============================================================================
# FILE: app/services/lead_service.py
# ============================================================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, asc, desc, join
from sqlalchemy.orm import selectinload, aliased
from typing import List, Tuple, Optional
from uuid import UUID

from app.models.lead import (
    Lead, LeadStatus, LeadCategory, EvidenceType, LeadInterest, InterestStatus
)
from app.models.user import User, UserRole, VendorProfile, BuyerProfile # Updated User models
from app.models.opportunity import Opportunity, OpportunityInterest # Using the new models
from app.models.opportunity import OpportunityStatus, OpportunityCategory # Updated enums
from app.schemas.lead import LeadCreateRequest, LeadInterestRequest, LeadResponse, LeadListResponse, LeadInterestResponse # Updated schemas
from app.services.pgp_service import pgp_service # Not directly used, but part of overall flow
from app.services.auth_service import AuthenticationError # For error consistency


class LeadError(Exception):
    """Custom exception for opportunity-related errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class LeadService:
    """Service for managing buyer opportunities."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_opportunity(self, buyer_id: UUID, request: LeadCreateRequest) -> Lead:
        """Create a new opportunity submission."""
        
        # Basic validation for enum values
        if not hasattr(OpportunityCategory, request.category.upper()):
            raise LeadError(f"Invalid opportunity category: {request.category}", status_code=422)
        for req in request.requirements:
            # Assuming requirements is a list of strings, no enum validation needed here unless defined
            pass 
        
        opportunity = Lead( # Using Lead model for now, might need refactor to Opportunity model later
            buyer_id=buyer_id,
            title=request.title,
            category=LeadCategory(request.category), # Using LeadCategory for now
            subcategory=request.subcategory,
            description=request.description,
            requirements=[str(r) for r in request.requirements], # Ensure strings
            geographic_scope=request.geographic_scope,
            budget_usd=request.budget_usd,
            status=LeadStatus.DRAFT, # Starts as draft
            # time_sensitivity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) # Keep this field
            time_sensitivity=request.time_sensitivity,
        )
        
        self.db.add(opportunity)
        await self.db.flush()
        return opportunity
    
    async def get_opportunity(self, opportunity_id: str) -> Lead:
        """Retrieve an opportunity by its ID."""
        stmt = select(Lead).where(Lead.id == opportunity_id)
        result = await self.db.execute(stmt)
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise LeadError("Opportunity not found", status_code=404)
        return opportunity
    
    async def get_opportunities_for_buyer(
        self,
        buyer_id: UUID,
        page: int,
        page_size: int,
        category: Optional[LeadCategory],
        status: Optional[LeadStatus],
    ) -> Tuple[List[Lead], int]:
        """Get opportunities submitted by a specific buyer."""
        stmt = select(Lead).where(Lead.buyer_id == buyer_id)
        
        # Filter by status and category for buyers (draft, submitted, published, matched)
        allowed_statuses = [LeadStatus.DRAFT, LeadStatus.SUBMITTED, LeadStatus.PUBLISHED, LeadStatus.MATCHED]
        if status and status not in allowed_statuses:
            status = None # Ignore invalid status for buyers
        
        if status:
            stmt = stmt.where(Lead.status == status)
        else:
            stmt = stmt.where(Lead.status.in_(allowed_statuses))
            
        if category:
            stmt = stmt.where(Lead.category == category)
        
        stmt = stmt.order_by(desc(Lead.submitted_at), desc(Lead.created_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        opportunities = result.scalars().all()
        
        return opportunities, total
    
    async def get_opportunities_for_vendor(
        self,
        vendor_id: Optional[UUID] = None, # Make optional for public browsing
        page: int = 1,
        page_size: int = 20,
        category: Optional[LeadCategory] = None,
        status: Optional[LeadStatus] = None,
    ) -> Tuple[List[Lead], int]:
        """Get opportunities available for vendors."""
        stmt = select(Lead).where(
            Lead.status.in_([LeadStatus.PUBLISHED, LeadStatus.MATCHED, LeadStatus.IN_PROGRESS])
        )
        
        if status:
            stmt = stmt.where(Lead.status == status)
        if category:
            stmt = stmt.where(Lead.category == category)
        
        # If vendor_id is provided, exclude opportunities they've already applied to or matched with
        if vendor_id:
            stmt = stmt.where(
                ~Lead.id.in_(
                    select(LeadInterest.opportunity_id).where( # Updated FK name
                        LeadInterest.vendor_id == vendor_id
                    )
                )
            ).where(Lead.accepted_vendor_id != vendor_id)
        
        # Join with VendorProfile to get shop name and rating for the accepted vendor
        # And join with User to get vendor username
        vendor_user_alias = aliased(User)
        vendor_profile_alias = aliased(VendorProfile)
        
        # For the accepted vendor
        stmt = stmt.outerjoin(vendor_user_alias, Lead.accepted_vendor_id == vendor_user_alias.id)
        stmt = stmt.outerjoin(vendor_profile_alias, vendor_user_alias.id == vendor_profile_alias.id)
        
        # Select only necessary columns for efficiency if needed
        stmt = stmt.options(
            selectinload(Lead.interests).joinedload(LeadInterest.vendor).joinedload(User.vendor_profile)
        )
        
        stmt = stmt.order_by(desc(Lead.submitted_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        opportunities = result.scalars().all()
        
        return opportunities, total

    async def get_all_opportunities(
        self,
        page: int,
        page_size: int,
        category: Optional[LeadCategory],
        status: Optional[LeadStatus],
    ) -> Tuple[List[Lead], int]:
        """ Get all opportunities, used by admins. """
        stmt = select(Lead)
        
        if status:
            stmt = stmt.where(Lead.status == status)
        if category:
            stmt = stmt.where(Lead.category == category)
        
        # Join with User and VendorProfile for accepted vendor info
        vendor_user_alias = aliased(User)
        vendor_profile_alias = aliased(VendorProfile)
        stmt = stmt.outerjoin(vendor_user_alias, Lead.accepted_vendor_id == vendor_user_alias.id)
        stmt = stmt.outerjoin(vendor_profile_alias, vendor_user_alias.id == vendor_profile_alias.id)

        stmt = stmt.order_by(desc(Lead.submitted_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        opportunities = result.scalars().all()
        
        return opportunities, total
    
    async def update_opportunity(
        self,
        buyer_id: UUID,
        opportunity_id: str,
        request: LeadCreateRequest,
    ) -> Lead:
        """Update an existing opportunity owned by the buyer."""
        opportunity = await self.get_opportunity(opportunity_id)
        
        if opportunity.buyer_id != buyer_id:
            raise LeadError("Opportunity not found", status_code=404)
        
        if opportunity.status != LeadStatus.DRAFT:
            raise LeadError("Opportunity can only be updated in draft status", status_code=400)
        
        # Validate category
        if not hasattr(LeadCategory, request.category.upper()):
            raise LeadError(f"Invalid opportunity category: {request.category}", status_code=422)
        
        opportunity.title = request.title
        opportunity.category = LeadCategory(request.category)
        opportunity.subcategory = request.subcategory
        opportunity.description = request.description
        opportunity.requirements = [str(r) for r in request.requirements]
        opportunity.geographic_scope = request.geographic_scope
        opportunity.budget_usd = request.budget_usd
        opportunity.time_sensitivity = request.time_sensitivity
        
        await self.db.flush()
        return opportunity
    
    async def submit_opportunity(self, buyer_id: UUID, opportunity_id: str) -> Lead:
        """Submit an opportunity for admin review."""
        opportunity = await self.get_opportunity(opportunity_id)
        
        if opportunity.buyer_id != buyer_id:
            raise LeadError("Opportunity not found", status_code=404)
        
        if opportunity.status != LeadStatus.DRAFT:
            raise LeadError("Opportunity is not in draft status and cannot be submitted", status_code=400)
        
        opportunity.status = LeadStatus.SUBMITTED
        opportunity.submitted_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return opportunity
    
    async def express_interest(
        self,
        vendor_id: UUID,
        opportunity_id: str,
        request: LeadInterestRequest,
    ) -> LeadInterest:
        """Vendor expresses interest in an opportunity."""
        opportunity = await self.get_opportunity(opportunity_id)
        
        # Check if opportunity is available for vendors
        if opportunity.status not in [LeadStatus.PUBLISHED]: # Only published opportunities can receive interest
            raise LeadError("Opportunity is not available for interest expression", status_code=400)
        
        # Check if already expressed interest or matched
        existing_interest = await self.get_interest_by_opportunity_and_vendor(opportunity_id, vendor_id)
        if existing_interest and existing_interest.status in [InterestStatus.ACCEPTED, InterestStatus.PENDING]:
            raise LeadError("You have already expressed interest in this opportunity", status_code=409)
        if opportunity.accepted_vendor_id == vendor_id:
            raise LeadError("You are already the accepted vendor for this opportunity", status_code=409)
            
        interest = LeadInterest(
            opportunity_id=opportunity.id, # Updated FK name
            vendor_id=vendor_id,
            pitch=request.pitch,
            status=InterestStatus.PENDING,
        )
        
        self.db.add(interest)
        await self.db.flush()
        return interest
    
    async def get_interest_by_opportunity_and_vendor(self, opportunity_id: str, vendor_id: UUID) -> Optional[LeadInterest]:
        """Retrieve a specific interest entry."""
        stmt = select(LeadInterest).where(
            LeadInterest.opportunity_id == opportunity_id, # Updated FK name
            LeadInterest.vendor_id == vendor_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_interests_for_opportunity(self, opportunity_id: str) -> List[LeadInterest]:
        """Get all interest expressions for an opportunity."""
        stmt = select(LeadInterest).where(LeadInterest.opportunity_id == opportunity_id) # Updated FK name
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # --- Model conversion methods ---
    
    def model_to_response(self, opportunity: Lead) -> LeadResponse:
        """Convert Lead (Opportunity) model to response schema."""
        from app.schemas.lead import LeadResponse
        
        # Fetch accepted vendor info if matched
        accepted_vendor_username = None
        accepted_vendor_shop_name = None
        accepted_vendor_alias = None
        vendor_interest_status = None
        
        if opportunity.accepted_vendor_id:
            # Load vendor details if available
            vendor_user = None
            if hasattr(opportunity, 'vendor') and opportunity.vendor:
                 vendor_user = opportunity.vendor
            
            if vendor_user:
                accepted_vendor_username = vendor_user.username
                if vendor_user.vendor_profile:
                    accepted_vendor_shop_name = vendor_user.vendor_profile.shop_name
            
            # Check interest status if vendor is accepted
            if opportunity.accepted_vendor_id:
                 # Need to fetch the specific interest to get status
                 # This requires another query or pre-loading; simplified here
                 pass # Placeholder for fetching interest status

        return LeadResponse(
            id=str(opportunity.id),
            title=opportunity.title,
            category=opportunity.category.value,
            subcategory=opportunity.subcategory,
            description=opportunity.description,
            requirements=[str(r) for r in opportunity.requirements],
            geographic_scope=opportunity.geographic_scope,
            budget_usd=opportunity.budget_usd,
            time_sensitivity=opportunity.time_sensitivity,
            status=opportunity.status.value,
            submitted_at=opportunity.submitted_at.isoformat() if opportunity.submitted_at else None,
            created_at=opportunity.created_at.isoformat(),
            
            vendor_interest_status=vendor_interest_status,
            accepted_vendor_username=accepted_vendor_username,
            accepted_vendor_shop_name=accepted_vendor_shop_name,
            accepted_vendor_alias=accepted_vendor_alias,
        )
    
    def interest_model_to_response(self, interest: LeadInterest) -> LeadInterestResponse:
        """Convert LeadInterest model to response schema."""
        from app.schemas.lead import LeadInterestResponse
        
        vendor_username = "Unknown"
        vendor_shop_name = None
        vendor_categories = None
        vendor_rating = 0.0
        
        if interest.vendor:
            vendor_username = interest.vendor.username
            if interest.vendor.vendor_profile:
                vendor_shop_name = interest.vendor.vendor_profile.shop_name
                vendor_categories = interest.vendor.vendor_profile.categories
                vendor_rating = interest.vendor.vendor_profile.rating
        
        return LeadInterestResponse(
            interest_id=str(interest.id),
            vendor_username=vendor_username,
            vendor_shop_name=vendor_shop_name,
            vendor_categories=vendor_categories,
            vendor_rating=vendor_rating,
            pitch=interest.pitch,
            status=interest.status.value,
            created_at=interest.created_at.isoformat(),
        )


# ============================================================================
# FILE: app/services/message_service.py
# ============================================================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, asc
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Tuple, Optional
from uuid import UUID
import hashlib

from app.models.message import Conversation, Message
from app.models.user import User, UserRole # For role checks and user details
from app.models.lead import Lead # To fetch opportunity titles
from app.services.pgp_service import pgp_service
from app.services.auth_service import AuthenticationError # For error consistency
from app.schemas.message import ConversationResponse, MessageResponse, ConversationDetailResponse


class MessageError(Exception):
    """Custom exception for message-related errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class MessageService:
    """Service for managing secure messages."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_conversations_for_user(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
    ) -> Tuple[List[Conversation], int]:
        """Get all conversations for a given user."""
        # Load related data needed for conversation response
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.messages) # To get unread count
            )
            .where(
                (Conversation.buyer_id == user_id) | (Conversation.vendor_id == user_id) # Updated FK names
            )
            .order_by(desc(Conversation.last_message_at)) # Order by most recent message
        )
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        conversations = result.scalars().all()
        
        return conversations, total
    
    async def get_conversation_by_id(self, conversation_id: str) -> Conversation:
        """Get a conversation by its ID."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise MessageError("Conversation not found", status_code=404)
        return conversation
    
    async def get_messages_for_conversation(self, conversation_id: str) -> List[Message]:
        """Get all messages within a conversation."""
        stmt = select(Message).where(Message.conversation_id == conversation_id)
        stmt = stmt.order_by(asc(Message.created_at)) # Order chronologically
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def send_message(
        self,
        conversation_id: str,
        sender_id: UUID,
        encrypted_content: str,
        content_hash: str,
    ) -> Message:
        """Send a new message to a conversation."""
        # Verify conversation exists and sender is part of it
        conversation = await self.get_conversation_by_id(conversation_id)
        
        if conversation.buyer_id != sender_id and conversation.vendor_id != sender_id: # Updated FK names
            raise MessageError("Sender is not part of this conversation", status_code=403)
        
        if conversation.closed_at:
            raise MessageError("Conversation is closed", status_code=400)
        
        # Basic content validation (assuming PGP format)
        if not encrypted_content.startswith("-----BEGIN PGP MESSAGE-----"):
             raise MessageError("Invalid message format", status_code=422)
        
        # Calculate hash if not provided or mismatch
        calculated_hash = hashlib.sha256(encrypted_content.encode()).hexdigest()
        if calculated_hash != content_hash:
            # This could indicate tampering or a client-side error
            # In a robust system, you might log this or handle differently
            # For now, we'll trust the client-provided hash if it matches what we calculate
            # This check might be redundant if content_hash is always derived from encrypted_content
            pass # Or raise error if strict check is desired.
        
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            encrypted_content=encrypted_content,
            content_hash=content_hash, # Use the hash provided by the client
        )
        
        self.db.add(message)
        await self.db.flush()
        
        # Update conversation's last message time
        conversation.last_message_at = message.created_at
        await self.db.flush()
        
        return message
    
    async def mark_messages_as_read(self, conversation_id: str, user_id: UUID) -> None:
        """Mark all unread messages in a conversation as read for the user."""
        # Get conversation to check user participation
        conversation = await self.get_conversation_by_id(conversation_id)
        if not (conversation.buyer_id == user_id or conversation.vendor_id == user_id): # Updated FK names
            return # User is not part of this conversation
        
        # Update messages where the sender is NOT the current user and they are unread
        stmt = (
            update(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.sender_id != user_id) # Messages sent by the other party
            .where(Message.read_at == None)
            .values(read_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.flush()
    
    # --- Model conversion methods ---
    
    def conversation_to_response(
        self,
        conversation: Conversation,
        current_user_id: UUID,
        opportunity_title: Optional[str] = None, # Updated parameter name
    ) -> ConversationResponse:
        """Convert Conversation model to response schema."""
        from app.schemas.message import ConversationResponse
        
        # Determine the other party
        other_party = None
        other_party_role = ""
        
        if conversation.buyer_id == current_user_id:
            # Current user is buyer, other is vendor
            other_party = getattr(conversation, 'vendor', None)
            if other_party:
                other_party_role = other_party.role.value
        elif conversation.vendor_id == current_user_id:
            # Current user is vendor, other is buyer
            other_party = getattr(conversation, 'buyer', None)
            if other_party:
                other_party_role = other_party.role.value
        
        other_party_username = other_party.username if other_party else "Unknown"
        
        # Calculate unread count
        unread_count = 0
        if conversation.messages:
            for msg in conversation.messages:
                if msg.sender_id != current_user_id and msg.read_at is None:
                    unread_count += 1
        
        return ConversationResponse(
            id=str(conversation.id),
            opportunity_id=str(conversation.opportunity_id) if conversation.opportunity_id else None, # Updated field name
            opportunity_title=opportunity_title, # Use passed title
            other_party_username=other_party_username,
            other_party_role=other_party_role,
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            unread_count=unread_count,
            is_closed=bool(conversation.closed_at),
        )
    
    def message_to_response(self, message: Message, current_user_id: UUID) -> MessageResponse:
        """Convert Message model to response schema."""
        from app.schemas.message import MessageResponse
        
        # Fetch sender username
        sender_username = "Unknown"
        if hasattr(message, 'sender') and message.sender:
            sender_username = message.sender.username
        
        return MessageResponse(
            id=str(message.id),
            sender_username=sender_username,
            sender_id=str(message.sender_id),
            is_mine=(message.sender_id == current_user_id),
            encrypted_content=message.encrypted_content,
            content_hash=message.content_hash,
            created_at=message.created_at.isoformat(),
            read_at=message.read_at.isoformat() if message.read_at else None,
        )


# ============================================================================
# FILE: app/services/listing_service.py
# ============================================================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, asc, literal_column
from sqlalchemy.orm import selectinload, aliased
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
import re # For slug generation

from app.models.listing import (
    SupportListing, ListingStatus, ListingCategory, SupportTier, # Renamed models
    SupportContribution, ContributionStatus, Review, ListingUpdate
)
from app.models.listing import VendorListing, VendorTier, Transaction, Review, ListingUpdate # Import new models
from app.models.user import User, UserRole, VendorProfile # Import User and VendorProfile
from app.schemas.listing import (
    ListingCreateRequest, ListingResponse, TierCreateRequest,
    TierResponse, ContributionCreateRequest, ContributionResponse,
    ReviewResponse, ListingUpdateResponse
)
from app.services.pgp_service import pgp_service # Not directly used, but for context
from app.services.monero_service import MoneroService, monero_service # For XMR amounts


class ListingError(Exception):
    """Custom exception for listing-related errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ListingService:
    """Service for managing vendor listings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_vendor_listing(self, vendor_id: UUID, request: ListingCreateRequest) -> VendorListing:
        """Create a new vendor listing."""
        
        # Validate category
        if not hasattr(ListingCategory, request.category.upper()):
            raise ListingError(f"Invalid listing category: {request.category}", status_code=422)
        
        # Generate slug
        slug = self._generate_slug(request.title)
        
        listing = VendorListing(
            vendor_id=vendor_id,
            title=request.title,
            slug=slug,
            category=ListingCategory(request.category),
            headline=request.headline,
            description=request.description, # Renamed from story
            disclosure_summary=request.disclosure_summary,
            risk_description=request.risk_description,
            price_usd_cents=request.price_usd_cents, # Use fixed price from request
            status=ListingStatus.DRAFT, # Starts as draft
        )
        
        self.db.add(listing)
        await self.db.flush()
        return listing
    
    async def get_listing_by_id(self, listing_id: str) -> VendorListing:
        """Retrieve a listing by its ID."""
        stmt = select(VendorListing).where(VendorListing.id == listing_id)
        result = await self.db.execute(stmt)
        listing = result.scalar_one_or_none()
        
        if not listing:
            raise ListingError("Listing not found", status_code=404)
        return listing
    
    async def get_listing_by_slug(self, slug: str) -> VendorListing:
        """Retrieve a listing by its slug."""
        stmt = select(VendorListing).where(VendorListing.slug == slug)
        result = await self.db.execute(stmt)
        listing = result.scalar_one_or_none()
        
        if not listing:
            raise ListingError("Listing not found", status_code=404)
        return listing
    
    async def get_listings(
        self,
        page: int,
        page_size: int,
        category: Optional[ListingCategory] = None,
        status: Optional[ListingStatus] = None,
        verified_by_admin: Optional[bool] = None,
    ) -> Tuple[List[VendorListing], int]:
        """Get a list of listings with optional filters."""
        stmt = select(VendorListing)
        
        # Join with VendorProfile and User to get vendor details
        vendor_user_alias = aliased(User)
        vendor_profile_alias = aliased(VendorProfile)
        stmt = stmt.outerjoin(vendor_user_alias, VendorListing.vendor_id == vendor_user_alias.id)
        stmt = stmt.outerjoin(vendor_profile_alias, vendor_user_alias.id == vendor_profile_alias.id)
        
        # Apply filters
        if status:
            stmt = stmt.where(VendorListing.status == status)
        if category:
            stmt = stmt.where(VendorListing.category == category)
        if verified_by_admin is not None:
            stmt = stmt.where(VendorListing.verified_by_admin == verified_by_admin)
        
        # Order by vendor status/rating if available, then creation date
        stmt = stmt.order_by(
            desc(VendorListing.verified_by_admin), # Verified first
            desc(vendor_profile_alias.rating.if_(0.0)), # Highest rated first
            desc(VendorListing.published_at),
            desc(VendorListing.created_at)
        )
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        listings = result.scalars().all()
        
        return listings, total
    
    async def get_listings_for_vendor(
        self,
        vendor_id: UUID,
        page: int,
        page_size: int,
        category: Optional[ListingCategory],
        status: Optional[ListingStatus],
    ) -> Tuple[List[VendorListing], int]:
        """Get listings submitted by a specific vendor."""
        stmt = select(VendorListing).where(VendorListing.vendor_id == vendor_id)
        
        if status:
            stmt = stmt.where(VendorListing.status == status)
        if category:
            stmt = stmt.where(VendorListing.category == category)
        
        # Join with VendorProfile and User for vendor details in response
        vendor_user_alias = aliased(User)
        vendor_profile_alias = aliased(VendorProfile)
        stmt = stmt.outerjoin(vendor_user_alias, VendorListing.vendor_id == vendor_user_alias.id)
        stmt = stmt.outerjoin(vendor_profile_alias, vendor_user_alias.id == vendor_profile_alias.id)
        
        stmt = stmt.order_by(desc(VendorListing.published_at), desc(VendorListing.created_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        listings = result.scalars().all()
        
        return listings, total
    
    async def update_vendor_listing(
        self,
        vendor_id: UUID,
        listing_id: str,
        request: ListingCreateRequest,
    ) -> VendorListing:
        """Update an existing vendor listing."""
        listing = await self.get_listing_by_id(listing_id)
        
        if listing.vendor_id != vendor_id:
            raise ListingError("Listing not found", status_code=404)
        
        if listing.status not in [ListingStatus.DRAFT, ListingStatus.PENDING_REVIEW]:
            raise ListingError("Listing can only be updated in draft or pending review status", status_code=400)
        
        # Validate category
        if not hasattr(ListingCategory, request.category.upper()):
            raise ListingError(f"Invalid listing category: {request.category}", status_code=422)
        
        # Generate new slug if title changed
        if listing.title != request.title:
            listing.slug = self._generate_slug(request.title)
        
        listing.title = request.title
        listing.category = ListingCategory(request.category)
        listing.headline = request.headline
        listing.description = request.description
        listing.disclosure_summary = request.disclosure_summary
        listing.risk_description = request.risk_description
        listing.price_usd_cents = request.price_usd_cents
        
        await self.db.flush()
        return listing
    
    async def submit_listing(self, vendor_id: UUID, listing_id: str) -> VendorListing:
        """Submit a listing for admin review."""
        listing = await self.get_listing_by_id(listing_id)
        
        if listing.vendor_id != vendor_id:
            raise ListingError("Listing not found", status_code=404)
        
        if listing.status != ListingStatus.DRAFT:
            raise ListingError("Listing is not in draft status and cannot be submitted", status_code=400)
        
        listing.status = ListingStatus.PENDING_REVIEW
        
        await self.db.flush()
        return listing
    
    async def add_vendor_tier(
        self,
        vendor_id: UUID,
        listing_id: str,
        request: TierCreateRequest,
    ) -> VendorTier:
        """Add a new tier to a vendor listing."""
        listing = await self.get_listing_by_id(listing_id)
        
        if listing.vendor_id != vendor_id:
            raise ListingError("Listing not found", status_code=404)
        
        if listing.status != ListingStatus.DRAFT:
            raise ListingError("Tiers can only be added to listings in draft status", status_code=400)
        
        tier = VendorTier(
            listing_id=listing.id,
            name=request.name,
            description=request.description,
            amount_usd=request.amount_usd,
            perks=request.perks or [],
            is_highlighted=request.is_highlighted,
            max_purchasers=request.max_purchasers,
            sort_order=await self.get_next_tier_sort_order(listing_id),
        )
        
        self.db.add(tier)
        await self.db.flush()
        return tier
    
    async def get_next_tier_sort_order(self, listing_id: UUID) -> int:
        """Get the next available sort order for a tier."""
        stmt = select(func.max(VendorTier.sort_order)).where(VendorTier.listing_id == listing_id)
        result = await self.db.execute(stmt)
        max_order = result.scalar_one_or_none()
        return (max_order or 0) + 1
    
    async def get_vendor_tier_by_id(self, tier_id: str) -> VendorTier:
        """Retrieve a tier by its ID."""
        stmt = select(VendorTier).where(VendorTier.id == tier_id)
        result = await self.db.execute(stmt)
        tier = result.scalar_one_or_none()
        
        if not tier:
            raise ListingError("Tier not found", status_code=404)
        return tier
    
    async def update_vendor_tier(
        self,
        vendor_id: UUID,
        listing_id: str,
        tier_id: str,
        request: TierCreateRequest,
    ) -> VendorTier:
        """Update an existing vendor tier."""
        listing = await self.get_listing_by_id(listing_id)
        if listing.vendor_id != vendor_id:
            raise ListingError("Listing not found", status_code=404)
        
        tier = await self.get_vendor_tier_by_id(tier_id)
        if tier.listing_id != listing.id:
            raise ListingError("Tier does not belong to this listing", status_code=400)
        
        if listing.status != ListingStatus.DRAFT:
            raise ListingError("Tiers can only be updated for listings in draft status", status_code=400)
        
        tier.name = request.name
        tier.description = request.description
        tier.amount_usd = request.amount_usd
        tier.perks = request.perks or []
        tier.is_highlighted = request.is_highlighted
        tier.max_purchasers = request.max_purchasers
        
        await self.db.flush()
        return tier
    
    async def get_tiers_for_listing(self, listing_id: UUID) -> List[VendorTier]:
        """Get all tiers associated with a vendor listing."""
        stmt = select(VendorTier).where(VendorTier.listing_id == listing_id)
        stmt = stmt.order_by(asc(VendorTier.sort_order))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_reviews_for_listing(self, listing_id: UUID) -> List[Review]:
        """Get all reviews for a vendor listing."""
        stmt = select(Review).where(Review.listing_id == listing_id)
        stmt = stmt.order_by(desc(Review.created_at))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_updates_for_listing(self, listing_id: UUID) -> List[ListingUpdate]:
        """Get all updates for a vendor listing."""
        stmt = select(ListingUpdate).where(ListingUpdate.listing_id == listing_id)
        stmt = stmt.order_by(desc(ListingUpdate.created_at))
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_transaction(
        self,
        listing_id: UUID,
        vendor_id: UUID,
        tier_id: Optional[UUID],
        buyer_user_id: Optional[UUID],
        buyer_alias: Optional[str],
        is_anonymous_buyer: bool,
        encrypted_message: Optional[str],
        deposit_id: UUID,
        amount_usd_cents: int,
        amount_xmr_atomic: int,
        exchange_rate_used: str,
    ) -> Transaction:
        """Create a record for a new transaction."""
        transaction = Transaction(
            listing_id=listing_id,
            vendor_id=vendor_id,
            tier_id=tier_id,
            buyer_user_id=buyer_user_id,
            buyer_alias=buyer_alias,
            is_anonymous_buyer=is_anonymous_buyer,
            encrypted_message=encrypted_message,
            deposit_id=deposit_id,
            amount_usd_cents=amount_usd_cents,
            amount_xmr_atomic=amount_xmr_atomic,
            exchange_rate_used=exchange_rate_used,
            status=ContributionStatus.PENDING, # Reusing enum
        )
        self.db.add(transaction)
        await self.db.flush()
        return transaction
    
    async def confirm_contribution( # This method relates to transactions now
        self,
        deposit_id: UUID,
        tx_hash: str,
        confirmed_at: datetime,
        received_amount_atomic: int,
        listing_id: UUID,
        tier_id: UUID,
    ) -> None:
        """Mark a transaction (contribution) as confirmed."""
        # Find the transaction associated with the deposit
        stmt = select(Transaction).where(Transaction.deposit_id == deposit_id)
        result = await self.db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            # Log this potential issue - deposit confirmed but no transaction found
            print(f"Warning: Deposit {deposit_id} confirmed, but no associated transaction found for listing {listing_id}, tier {tier_id}.")
            return
        
        # Update transaction status and details
        transaction.status = ContributionStatus.CONFIRMED
        transaction.confirmed_at = confirmed_at
        transaction.tx_hash = tx_hash
        # received_amount_atomic should match expected amount ideally, but we store it here too
        transaction.received_amount_atomic = received_amount_atomic # Store actual received amount
        
        # Update listing totals
        listing = await self.get_listing_by_id(str(listing_id))
        if listing:
            listing.total_raised_atomic += received_amount_atomic # Use actual received amount
            listing.supporter_count += 1 # Increment purchaser count
            
            # Update tier purchaser count if tier specified
            if tier_id:
                tier = await self.get_vendor_tier_by_id(str(tier_id))
                if tier:
                    tier.current_purchasers += 1
        
        await self.db.flush()
    
    async def add_listing_update(
        self,
        vendor_id: UUID,
        listing_id: str,
        title: str,
        content: str,
        minimum_tier_amount: int,
    ) -> ListingUpdate:
        """Add a progress update to a vendor listing."""
        listing = await self.get_listing_by_id(listing_id)
        if listing.vendor_id != vendor_id:
            raise ListingError("Listing not found", status_code=404)
        
        if listing.status not in [ListingStatus.ACTIVE, ListingStatus.PAUSED]:
            raise ListingError("Updates can only be added to active or paused listings", status_code=400)
        
        update = ListingUpdate(
            listing_id=listing.id,
            title=title,
            content=content,
            minimum_tier_amount=minimum_tier_amount,
        )
        self.db.add(update)
        await self.db.flush()
        return update
    
    async def increment_view_count(self, listing_id: UUID):
        """Increment the view count for a listing."""
        stmt = (
            update(VendorListing) # Use VendorListing model
            .where(VendorListing.id == listing_id)
            .values(view_count=VendorListing.view_count + 1)
        )
        await self.db.execute(stmt)
        await self.db.flush()
    
    # --- Slug generation ---
    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from a title."""
        slug = re.sub(r"[^\w\s-]", "", title).strip().lower()
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug
    
    # --- Model conversion methods ---
    
    def model_to_response(self, listing: VendorListing) -> ListingResponse:
        """Convert VendorListing model to response schema."""
        from app.schemas.listing import ListingResponse
        from app.services.monero_service import monero_service # For display purposes
        
        vendor_username = "Unknown"
        vendor_shop_name = None
        vendor_rating = 0.0
        
        if listing.vendor:
            vendor_username = listing.vendor.username
            if listing.vendor.vendor_profile:
                vendor_shop_name = listing.vendor.vendor_profile.shop_name
                vendor_rating = listing.vendor.vendor_profile.rating
        
        return ListingResponse(
            id=str(listing.id),
            slug=listing.slug,
            title=listing.title,
            category=listing.category.value,
            headline=listing.headline,
            description=listing.description,
            disclosure_summary=listing.disclosure_summary,
            risk_description=listing.risk_description,
            price_usd_cents=listing.price_usd_cents,
            price_usd_display=f"${listing.price_usd_cents / 100.0:.2f}" if listing.price_usd_cents else None,
            verified=listing.verified_by_admin,
            status=listing.status.value,
            created_at=listing.created_at.isoformat(),
            published_at=listing.published_at.isoformat() if listing.published_at else None,
            vendor_username=vendor_username,
            vendor_shop_name=vendor_shop_name,
            vendor_rating=vendor_rating,
        )
    
    def tier_to_response(self, tier: VendorTier) -> TierResponse:
        """Convert VendorTier model to response schema."""
        from app.schemas.listing import TierResponse
        
        return TierResponse(
            id=str(tier.id),
            name=tier.name,
            description=tier.description,
            amount_usd=tier.amount_usd,
            amount_display=f"${tier.amount_usd / 100.0:.2f}",
            perks=tier.perks,
            is_highlighted=tier.is_highlighted,
            purchasers_remaining=tier.spots_remaining,
            is_available=tier.is_available,
        )
    
    def transaction_to_response(self, transaction: Transaction) -> ContributionResponse:
        """Convert Transaction model to response schema."""
        from app.schemas.listing import ContributionResponse
        from app.services.monero_service import monero_service
        
        tier_name = "N/A"
        if transaction.tier:
            tier_name = transaction.tier.name
        
        listing_title = "N/A"
        if transaction.listing:
            listing_title = transaction.listing.title
        
        vendor_shop_name = "Unknown Vendor"
        if transaction.listing and transaction.listing.vendor and transaction.listing.vendor.vendor_profile:
            vendor_shop_name = transaction.listing.vendor.vendor_profile.shop_name
        
        return ContributionResponse(
            transaction_id=str(transaction.id),
            listing_title=listing_title,
            vendor_shop_name=vendor_shop_name,
            tier_name=tier_name,
            amount_usd=f"{Decimal(transaction.amount_usd_cents) / 100:.2f}",
            amount_xmr=f"{monero_service.atomic_to_xmr(transaction.amount_xmr_atomic):.8f}",
            xmr_address=transaction.deposit.address if transaction.deposit else None,
            payment_id=transaction.deposit.payment_id if transaction.deposit else None,
            qr_code_base64=transaction.deposit.qr_code_base64 if transaction.deposit else None,
            expires_at=transaction.deposit.expires_at.isoformat() if transaction.deposit else None,
            exchange_rate=transaction.exchange_rate_used,
            status=transaction.status.value,
        )
    
    def review_to_response(self, review: Review) -> ReviewResponse:
        """Convert Review model to response schema."""
        from app.schemas.listing import ReviewResponse
        
        reviewer_alias = "Anonymous"
        if not review.is_anonymous and review.reviewer:
            reviewer_alias = review.reviewer.username
            if review.reviewer_alias: # Use alias if provided by reviewer
                reviewer_alias = review.reviewer_alias
        
        return ReviewResponse(
            id=str(review.id),
            listing_id=str(review.listing_id),
            transaction_id=str(review.transaction_id),
            reviewer_alias=reviewer_alias,
            rating=review.rating,
            comment=review.comment,
            is_anonymous=review.is_anonymous,
            created_at=review.created_at.isoformat(),
        )
    
    def update_to_response(self, update: ListingUpdate) -> ListingUpdateResponse:
        """Convert ListingUpdate model to response schema."""
        from app.schemas.listing import ListingUpdateResponse
        
        return ListingUpdateResponse(
            id=str(update.id),
            listing_id=str(update.listing_id),
            title=update.title,
            content=update.content,
            minimum_tier_amount=update.minimum_tier_amount,
            media_ids=update.media_ids,
            created_at=update.created_at.isoformat(),
        )

    # --- Helper methods for transaction confirmation ---
    async def confirm_transaction(
        self,
        deposit_id: UUID,
        tx_hash: str,
        confirmed_at: datetime,
        received_amount_atomic: int,
    ) -> None:
        """Confirms a transaction related to a deposit."""
        # Find the transaction associated with the deposit
        stmt = select(Transaction).where(Transaction.deposit_id == deposit_id)
        result = await self.db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            # Log this potential issue - deposit confirmed but no transaction found
            print(f"Warning: Deposit {deposit_id} confirmed, but no associated transaction found.")
            return
        
        # Update transaction status and details
        transaction.status = ContributionStatus.CONFIRMED
        transaction.confirmed_at = confirmed_at
        transaction.tx_hash = tx_hash
        transaction.received_amount_atomic = received_amount_atomic # Store actual received amount
        
        # Update listing totals and tier purchaser count
        listing = await self.get_listing_by_id(str(transaction.listing_id))
        if listing:
            listing.total_raised_atomic += received_amount_atomic
            listing.supporter_count += 1 # Increment purchaser count
            
            if transaction.tier_id:
                tier = await self.get_vendor_tier_by_id(str(transaction.tier_id))
                if tier:
                    tier.current_purchasers += 1
        
        await self.db.flush()

# ============================================================================
# FILE: app/services/subscription_service.py
# ============================================================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, asc
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models.payment import Subscription, SubscriptionTier, SubscriptionStatus
from app.models.user import User, UserRole
from app.config import settings
from app.services.monero_service import MoneroService, monero_service
from app.services.price_oracle import PriceOracleError, price_oracle
from app.schemas.payment import SubscriptionResponse # Reusing schema


class SubscriptionError(Exception):
    """Custom exception for subscription-related errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SubscriptionService:
    """Service for managing vendor subscriptions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_subscription(
        self,
        user_id: UUID,
        tier: str,
        price_usd_cents: int,
        price_xmr_atomic: Optional[int],
        payment_method: str,
        payment_reference: Optional[str], # e.g., deposit ID for Monero, Stripe charge ID
    ) -> Subscription:
        """Create a new subscription record."""
        
        # Check if user already has an active subscription for this tier
        existing_sub = await self.get_active_subscription_for_user(user_id)
        if existing_sub and existing_sub.tier == SubscriptionTier(tier):
             # If renewing, update expiration and status
            if existing_sub.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRING]:
                # Extend subscription duration
                existing_sub.expires_at = existing_sub.expires_at + timedelta(days=30) # Assuming monthly billing
                existing_sub.price_usd_cents = price_usd_cents
                existing_sub.price_xmr_atomic = price_xmr_atomic
                existing_sub.payment_method = payment_method
                existing_sub.payment_reference = payment_reference
                existing_sub.status = SubscriptionStatus.ACTIVE # Ensure active status
                await self.db.flush()
                return existing_sub
            else:
                 # Handle cases like expired or cancelled, potentially creating a new one
                 pass # Fall through to create new if not active/expiring

        # Create a new subscription
        expires_at = datetime.now(timezone.utc) + timedelta(days=30) # Monthly billing
        
        subscription = Subscription(
            user_id=user_id,
            tier=SubscriptionTier(tier),
            price_usd_cents=price_usd_cents,
            price_xmr_atomic=price_xmr_atomic,
            started_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            status=SubscriptionStatus.ACTIVE, # Assume active upon successful payment initiation
            auto_renew=True, # Default to auto-renew
            payment_method=payment_method,
            payment_reference=payment_reference,
        )
        
        self.db.add(subscription)
        await self.db.flush()
        return subscription
    
    async def get_active_subscription_for_user(self, user_id: UUID) -> Optional[Subscription]:
        """Get the currently active subscription for a vendor."""
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRING]),
            Subscription.expires_at > datetime.now(timezone.utc) - timedelta(days=3) # Allow for slight clock skew or grace period
        ).order_by(desc(Subscription.expires_at)) # Get the latest expiring one if multiple somehow exist
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def cancel_subscription(self, user_id: UUID) -> bool:
        """Mark a subscription as cancelled."""
        # Find the latest active subscription
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRING]),
            Subscription.expires_at > datetime.now(timezone.utc)
        ).order_by(desc(Subscription.expires_at))
        
        result = await self.db.execute(stmt)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise SubscriptionError("No active subscription found to cancel", status_code=404)
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.auto_renew = False
        
        await self.db.flush()
        return True
    
    # --- Model conversion methods ---
    
    def model_to_response(
        self,
        subscription: Subscription,
        deposit_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Convert Subscription model to response schema."""
        from app.schemas.payment import SubscriptionResponse
        from app.services.monero_service import monero_service
        
        price_xmr_str = "N/A"
        if subscription.price_xmr_atomic:
            price_xmr_str = f"{monero_service.atomic_to_xmr(subscription.price_xmr_atomic):.8f}"
        
        return SubscriptionResponse(
            user_id=str(subscription.user_id),
            tier=subscription.tier.value,
            price_usd=f"{Decimal(subscription.price_usd_cents) / 100.0:.2f}",
            price_xmr=price_xmr_str,
            started_at=subscription.started_at.isoformat(),
            expires_at=subscription.expires_at.isoformat(),
            status=subscription.status.value,
            auto_renew=subscription.auto_renew,
            payment_method=subscription.payment_method,
            payment_reference=subscription.payment_reference,
            deposit_details=deposit_details, # Include Monero payment details if available
        )


# ============================================================================
# FILE: app/services/admin_service.py
# ============================================================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, asc, join, outerjoin, aliased
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from app.models.user import User, UserRole, VerificationStatus, VendorProfile, BuyerProfile # Added Vendor/Buyer profiles
from app.models.lead import Lead, LeadStatus # Renamed Lead to Opportunity
from app.models.listing import VendorListing, ListingStatus # Renamed SupportListing to VendorListing
from app.services.auth_service import AuthenticationError # For consistent error handling
from app.schemas.admin import (
    AdminLeadResponse, AdminVendorResponse, AdminListingResponse, # Renamed responses
    UserManagementResponse, UserDetailResponse, AdminReviewResponse
)


class AdminError(Exception):
    """Custom exception for admin-related errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AdminService:
    """Service for administrative tasks."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_opportunities_by_status( # Updated method name
        self,
        status: LeadStatus, # Still using LeadStatus enum for now
        page: int,
        page_size: int,
    ) -> Tuple[List[Lead], int]:
        """Get opportunities based on their status."""
        stmt = select(Lead).where(Lead.status == status) # Using Lead model for opportunities
        
        # Join with User to get buyer username
        stmt = stmt.options(joinedload(Lead.buyer)) # Load buyer user object
        
        stmt = stmt.order_by(desc(Lead.submitted_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        opportunities = result.scalars().all()
        
        return opportunities, total
    
    async def review_opportunity( # Updated method name
        self,
        opportunity_id: str,
        new_status: LeadStatus,
        admin_user_id: UUID,
        review_notes: Optional[str] = None,
    ) -> Lead: # Return type is Lead (Opportunity)
        """Approve or reject an opportunity."""
        stmt = select(Lead).where(Lead.id == opportunity_id)
        result = await self.db.execute(stmt)
        opportunity = result.scalar_one_or_none()
        
        if not opportunity:
            raise AdminError("Opportunity not found", status_code=404)
        
        if opportunity.status not in [LeadStatus.SUBMITTED, LeadStatus.UNDER_REVIEW]: # Check relevant statuses
            raise AdminError("Opportunity is not in a reviewable state", status_code=400)
        
        opportunity.status = new_status
        opportunity.reviewed_by = admin_user_id
        opportunity.reviewed_at = datetime.now(timezone.utc)
        opportunity.review_notes = review_notes
        
        await self.db.flush()
        return opportunity
    
    async def get_users_by_role_and_verification(
        self,
        role: UserRole,
        verification_status: Optional[VerificationStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[User], int]:
        """Get users filtered by role and verification status."""
        stmt = select(User)
        
        if role == UserRole.VENDOR:
            stmt = stmt.options(joinedload(User.vendor_profile)) # Load vendor profile for verification status
            stmt = stmt.where(User.role == UserRole.VENDOR)
            if verification_status:
                stmt = stmt.where(User.vendor_profile.has(VendorProfile.verification_status == verification_status))
        elif role == UserRole.BUYER:
             # Buyers may have profiles but not verification status in the same way
             # If filtering is needed, adjust this logic
             stmt = stmt.where(User.role == UserRole.BUYER)
        else:
            # Handle other roles if needed
             pass
        
        stmt = stmt.order_by(desc(User.created_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        users = result.scalars().all()
        
        return users, total
    
    async def verify_user_verification(
        self,
        user_id: str,
        new_status: VerificationStatus,
        admin_user_id: UUID,
        review_notes: Optional[str] = None,
    ) -> User:
        """Verify or reject a user's verification status (e.g., vendor)."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise AdminError("User not found", status_code=404)
        
        if user.role == UserRole.VENDOR:
            if not hasattr(user, 'vendor_profile') or not user.vendor_profile:
                raise AdminError("Vendor profile not found", status_code=404)
            
            user.vendor_profile.verification_status = new_status
            user.vendor_profile.verified_at = datetime.now(timezone.utc)
            user.vendor_profile.verified_by = admin_user_id
            user.vendor_profile.verification_notes = review_notes
        else:
            # Handle other roles if necessary
            raise AdminError("User role does not support verification status updates", status_code=400)
        
        await self.db.flush()
        return user
    
    async def get_listings_by_status(
        self,
        status: ListingStatus,
        page: int,
        page_size: int,
    ) -> Tuple[List[VendorListing], int]:
        """Get vendor listings based on their status."""
        stmt = select(VendorListing).where(VendorListing.status == status)
        
        # Join with User to get vendor username
        stmt = stmt.options(joinedload(VendorListing.vendor)) # Load vendor user object
        
        stmt = stmt.order_by(desc(VendorListing.submitted_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        listings = result.scalars().all()
        
        return listings, total
    
    async def review_listing(
        self,
        listing_id: str,
        new_status: ListingStatus,
        admin_user_id: UUID,
    ) -> VendorListing:
        """Approve or reject a vendor listing."""
        stmt = select(VendorListing).where(VendorListing.id == listing_id)
        result = await self.db.execute(stmt)
        listing = result.scalar_one_or_none()
        
        if not listing:
            raise AdminError("Listing not found", status_code=404)
        
        if listing.status != ListingStatus.PENDING_REVIEW:
            raise AdminError("Listing is not in pending review state", status_code=400)
        
        listing.status = new_status
        listing.verified_by_admin = True # Mark as admin verified
        listing.verified_at = datetime.now(timezone.utc)
        listing.verified_by = admin_user_id
        
        # Set published_at if activating
        if new_status == ListingStatus.ACTIVE:
            listing.published_at = datetime.now(timezone.utc)
        
        await self.db.flush()
        return listing
    
    async def get_users(
        self,
        page: int,
        page_size: int,
        role: Optional[UserRole] = None,
        verification_status: Optional[VerificationStatus] = None,
        search_query: Optional[str] = None,
    ) -> Tuple[List[User], int]:
        """Get users with various filters."""
        stmt = select(User)
        
        # Eager load profiles for verification status and other details
        stmt = stmt.options(
            selectinload(User.vendor_profile),
            selectinload(User.buyer_profile),
        )
        
        if role:
            stmt = stmt.where(User.role == role)
        
        if verification_status and role == UserRole.VENDOR:
            stmt = stmt.where(User.vendor_profile.has(VendorProfile.verification_status == verification_status))
        
        if search_query:
            search_query_lower = search_query.lower()
            stmt = stmt.where(
                (func.lower(User.username).contains(search_query_lower)) |
                (func.lower(User.pgp_fingerprint).contains(search_query_lower))
            )
        
        stmt = stmt.order_by(desc(User.created_at))
        
        total_stmt = stmt.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()
        
        result = await self.db.execute(
            stmt.limit(page_size).offset((page - 1) * page_size)
        )
        users = result.scalars().all()
        
        return users, total
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get a user by their ID."""
        stmt = select(User).where(User.id == user_id)
        stmt = stmt.options(
            selectinload(User.vendor_profile),
            selectinload(User.buyer_profile),
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise AdminError("User not found", status_code=404)
        return user
    
    async def update_user_status(self, user_id: str, is_active: bool) -> User:
        """Suspend or unsuspend a user."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise AdminError("User not found", status_code=404)
        
        user.is_active = is_active
        await self.db.flush()
        return user
    
    # --- Model conversion methods ---
    
    def opportunity_to_admin_response(self, opportunity: Lead) -> Dict[str, Any]: # Renamed response type
        """Convert Lead (Opportunity) model to admin response schema."""
        from app.schemas.admin import AdminLeadResponse
        
        buyer_username = opportunity.buyer.username if hasattr(opportunity, 'buyer') and opportunity.buyer else "Unknown"
        
        return AdminLeadResponse(
            id=str(opportunity.id),
            title=opportunity.title,
            buyer_username=buyer_username,
            category=opportunity.category.value,
            status=opportunity.status.value,
            submitted_at=opportunity.submitted_at.isoformat() if opportunity.submitted_at else None,
            review_notes=opportunity.review_notes,
            reviewed_at=opportunity.reviewed_at.isoformat() if opportunity.reviewed_at else None,
            reviewed_by_username=opportunity.reviewer.username if hasattr(opportunity, 'reviewer') and opportunity.reviewer else None,
        )
    
    def vendor_to_admin_response(self, user: User) -> Dict[str, Any]:
        """Convert User (Vendor) model to admin response schema."""
        from app.schemas.admin import AdminVendorResponse
        
        profile = user.vendor_profile
        if not profile:
            raise ValueError("User is not a vendor or profile missing") # Should not happen if called correctly
        
        return AdminVendorResponse(
            user_id=str(user.id),
            username=user.username,
            shop_name=profile.shop_name,
            verification_status=profile.verification_status.value,
            applied_at=user.created_at.isoformat(),
            verified_at=profile.verified_at.isoformat() if profile.verified_at else None,
            verified_by_username=user.verified_by_user.username if hasattr(user, 'verified_by_user') and user.verified_by_user else None, # Linked via verified_by
            review_notes=profile.verification_notes,
        )
    
    def listing_to_admin_response(self, listing: VendorListing) -> Dict[str, Any]:
        """Convert VendorListing model to admin response schema."""
        from app.schemas.admin import AdminListingResponse
        
        vendor_username = listing.vendor.username if hasattr(listing, 'vendor') and listing.vendor else "Unknown"
        
        return AdminListingResponse(
            id=str(listing.id),
            title=listing.title,
            vendor_username=vendor_username,
            category=listing.category.value,
            status=listing.status.value,
            submitted_at=listing.created_at.isoformat(), # Assuming submitted_at = created_at for pending
            verified=listing.verified_by_admin,
            verified_at=listing.verified_at.isoformat() if listing.verified_at else None,
            verified_by_username=listing.verifier.username if hasattr(listing, 'verifier') and listing.verifier else None, # Linked via verified_by
        )
    
    def user_to_management_response(self, user: User) -> Dict[str, Any]:
        """Convert User model to management response schema."""
        from app.schemas.admin import UserManagementResponse
        
        profile_details = {}
        if user.vendor_profile:
            profile_details = {
                "shop_name": user.vendor_profile.shop_name,
                "verification_status": user.vendor_profile.verification_status.value,
            }
        elif user.buyer_profile:
            profile_details = {
                "anonymous_alias": user.buyer_profile.anonymous_alias,
            }
            
        return UserManagementResponse(
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            profile_details=profile_details,
        )
    
    def user_to_detail_response(self, user: User) -> Dict[str, Any]:
        """Convert User model to detailed response schema."""
        from app.schemas.admin import UserDetailResponse
        
        profile_details = {}
        if user.vendor_profile:
            profile_details = {
                "shop_name": user.vendor_profile.shop_name,
                "description": user.vendor_profile.description,
                "categories": user.vendor_profile.categories,
                "verification_status": user.vendor_profile.verification_status.value,
                "organization_verified": user.vendor_profile.verified_at, # Assuming verified_at implies org verification? Or needs separate field.
                "verified_at": user.vendor_profile.verified_at.isoformat() if user.vendor_profile.verified_at else None,
                "verified_by_username": user.verified_by_user.username if hasattr(user, 'verified_by_user') and user.verified_by_user else None,
                "review_notes": user.vendor_profile.verification_notes,
                "subscription_tier": user.vendor_profile.subscription_tier,
                "subscription_expires_at": user.vendor_profile.subscription_expires_at.isoformat() if user.vendor_profile.subscription_expires_at else None,
                "total_sales": user.vendor_profile.total_sales,
                "rating": user.vendor_profile.rating,
            }
        elif user.buyer_profile:
            profile_details = {
                "anonymous_alias": user.buyer_profile.anonymous_alias,
                "trust_score": user.buyer_profile.trust_score,
            }
            
        return UserDetailResponse(
            user_id=str(user.id),
            username=user.username,
            role=user.role.value,
            pgp_fingerprint=user.pgp_fingerprint,
            is_active=user.is_active,
            threat_score=user.threat_score,
            created_at=user.created_at.isoformat(),
            last_seen_at=user.last_seen_at.isoformat() if user.last_seen_at else None,
            profile_details=profile_details,
        )


# ============================================================================
# FILE: app/workers/celery_app.py
# ============================================================================
from celery import Celery

from app.config import settings


# Initialize Celery application
celery_app = Celery(
    "architect_vault_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.payment_monitor",
        "app.workers.cleanup",
        # Add other worker modules here
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Optional: Autodiscover tasks from the include list
# celery_app.autodiscover_tasks()


# ============================================================================
# FILE: app/workers/payment_monitor.py
# ============================================================================
import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_

from app.database import get_db, async_session_factory
from app.models.payment import Deposit, DepositStatus, DepositPurpose, Subscription, SubscriptionStatus
from app.models.listing import VendorListing, VendorTier, Transaction # Updated models
from app.services.monero_service import MoneroService, monero_service
from app.services.price_oracle import PriceOracleError, price_oracle
from app.config import settings
from app.services.listing_service import ListingService # For confirming transactions


@shared_task(bind=True, max_retries=5, default_retry_delay=60) # Retry for transient errors
async def monitor_monero_deposits(self, *args, **kwargs):
    """
    Celery task to monitor Monero deposits for confirmations.
    Runs periodically to check for new transactions.
    """
    # Get a database session
    async_session = async_session_factory()
    db: AsyncSession = async_session.get_synchronizer().async_session
    
    try:
        # Find pending or confirming deposits that haven't expired
        stmt = select(Deposit).where(
            Deposit.status.in_([DepositStatus.PENDING, DepositStatus.CONFIRMING]),
            Deposit.expires_at > datetime.now(timezone.utc),
        )
        result = await db.execute(stmt)
        deposits = result.scalars().all()
        
        # Fetch current Monero price for potential recalculations or logging
        try:
            current_xmr_usd_price = await price_oracle.get_xmr_usd_price()
        except PriceOracleError:
            current_xmr_usd_price = None # Ignore if price oracle fails
        
        # Get recent transfers from Monero daemon
        # We only need transfers that match our payment IDs and addresses
        transfers_data = await monero_service.get_transfers(include_pool=True)
        if not transfers_data or "transfers" not in transfers_data:
            # No transfers found or error, skip processing this time
            # Celery will retry if configured
            return {"status": "No transfers found, retrying later."}
        
        processed_deposits = set()
        listing_service = ListingService(db) # Initialize ListingService for confirmations
        
        for deposit in deposits:
            # Check if this deposit has already been processed in this run to avoid duplicates
            if deposit.id in processed_deposits:
                continue
            
            expected_amount = deposit.expected_amount_atomic
            payment_id = deposit.payment_id
            address = deposit.address
            
            # Search for matching transfers
            matched_transfer = None
            for transfer in transfers_data.get("transfers", []):
                # Check if the transfer has a matching payment ID
                if transfer.get("payment_id") == payment_id:
                    # Check if the transfer amount matches the expected amount
                    # Allow for slight variations due to fees
