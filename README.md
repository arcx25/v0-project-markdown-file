# ARCHITECT - Anonymous XMR Marketplace

**Secure marketplace platform connecting buyers with verified vendors through PGP-authenticated, end-to-end encrypted channels.**

## Overview

ARCHITECT is a production-ready anonymous darknet marketplace featuring:

- **PGP-based authentication** - No passwords, cryptographic proof of identity
- **End-to-end encryption** - All messages encrypted with recipient's public key
- **Tor-only access** - Hidden service (.onion) for maximum anonymity
- **Monero payments** - XMR-only transactions for complete payment privacy
- **Opportunity marketplace** - Buyers post needs, vendors submit proposals
- **Escrow system** - Multi-signature escrow for transaction protection
- **Vendor verification** - Admin-verified sellers with reputation tracking
- **Subscription tiers** - Tiered vendor access (Free, Professional, Enterprise)

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- Redis 7.2
- GnuPG 2.4+
- Monero wallet RPC (for payments)
- Docker & Docker Compose (for containerized deployment)

### Environment Setup

1. Copy the environment template:
\`\`\`bash
cp .env.example .env
\`\`\`

2. Generate a secret key:
\`\`\`bash
openssl rand -hex 32
\`\`\`

3. Configure environment variables in `.env`:
   - `SECRET_KEY` - Application secret (64+ characters)
   - `DATABASE_URL` - PostgreSQL connection string
   - `REDIS_URL` - Redis connection string
   - `GPG_HOME_DIR` - GPG keyring directory
   - `MONERO_WALLET_RPC_URL` - Monero wallet RPC endpoint
   - See `.env.example` for complete configuration

### Installation

#### Using Docker Compose (Recommended)

\`\`\`bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access application at http://localhost:8000
\`\`\`

#### Manual Installation

\`\`\`bash
# Install dependencies
pip install -e .

# Initialize database
alembic upgrade head

# Create initial admin user
python scripts/init_admin.py

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Start Celery worker (in separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Start Celery beat (in separate terminal)
celery -A app.workers.celery_app beat --loglevel=info
\`\`\`

## Architecture

### Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 16 with asyncpg
- **Cache/Queue**: Redis 7.2, Celery
- **Encryption**: GnuPG 2.4+ for PGP operations
- **Payments**: Monero (XMR) via wallet RPC
- **Anonymity**: Tor hidden service
- **Templates**: Jinja2

### User Roles

- **Buyer**: Posts opportunities, reviews vendor proposals, initiates purchases
- **Vendor**: Browses opportunities, submits proposals, creates product listings
- **Admin**: Verifies vendors, moderates content, resolves disputes

### Project Structure

\`\`\`
vault/
├── app/
│   ├── api/              # REST API endpoints
│   │   ├── auth.py       # Authentication
│   │   ├── leads.py      # Lead management
│   │   ├── messages.py   # Secure messaging
│   │   ├── listings.py   # Support listings
│   │   ├── subscriptions.py  # Vendor subscriptions
│   │   └── admin.py      # Admin moderation
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── auth_service.py
│   │   ├── pgp_service.py
│   │   ├── monero_service.py
│   │   ├── notification_service.py
│   │   └── subscription_service.py
│   ├── workers/          # Background tasks
│   │   ├── payment_monitor.py
│   │   └── cleanup.py
│   ├── web/              # Web frontend routes
│   ├── templates/        # HTML templates
│   ├── static/           # CSS, JS, assets
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   └── main.py           # Application entry
├── deploy/               # Deployment scripts
│   ├── scripts/          # Setup and deployment automation
│   ├── config/           # Service configurations
│   └── avalanche/        # Avalanche server deployment
├── scripts/              # Utility scripts
├── tests/                # Test suite
├── docker-compose.yml    # Docker services
├── Dockerfile            # Container image
└── pyproject.toml        # Python dependencies
\`\`\`

## API Documentation

Once running, access interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

**Authentication**
- `POST /api/auth/register/challenge` - Initiate registration
- `POST /api/auth/register/verify` - Complete registration with PGP signature
- `POST /api/auth/login/challenge` - Initiate login
- `POST /api/auth/login/verify` - Complete login with PGP signature

**Marketplace Opportunities**
- `GET /api/leads` - Browse active opportunities (vendor)
- `POST /api/leads` - Create opportunity (buyer)
- `POST /api/leads/{id}/interest` - Submit proposal (vendor)
- `POST /api/leads/{id}/accept/{vendor_id}` - Accept vendor (buyer)

**Product Listings**
- `GET /api/listings` - Browse vendor listings (public)
- `POST /api/listings` - Create listing (vendor)
- `POST /api/listings/{slug}/purchase` - Initiate purchase

**Messages**
- `GET /api/conversations` - List encrypted conversations
- `GET /api/conversations/{id}/messages` - Get messages
- `POST /api/conversations/{id}/messages` - Send encrypted message

**Subscriptions**
- `GET /api/subscriptions/tiers` - View vendor subscription tiers
- `POST /api/subscriptions/subscribe` - Subscribe to tier
- `POST /api/subscriptions/upgrade` - Upgrade subscription
- `POST /api/subscriptions/cancel` - Cancel subscription

**Admin**
- `GET /api/admin/leads/pending` - Pending opportunities
- `POST /api/admin/leads/{id}/approve` - Approve opportunity
- `GET /api/admin/vendors/pending` - Pending vendor verifications
- `POST /api/admin/vendors/{id}/verify` - Verify vendor

## Security

### ARCHITECT Protocol

PGP-based challenge-response authentication:
1. User requests challenge with username
2. Server generates random challenge string
3. User signs challenge with PGP private key
4. Server verifies signature against public key
5. Session token issued on successful verification

### Encryption

- **Messages**: End-to-end encrypted with recipient's PGP public key
- **Transport**: TLS 1.3 for all connections
- **Storage**: LUKS full-disk encryption recommended
- **Sessions**: Cryptographic tokens with circuit binding

### Privacy

- No IP address logging
- Tor circuit binding for session security
- Anonymous Monero payments (no blockchain trail)
- Minimal metadata collection
- Single-use payment addresses

## Deployment

### Quick Deploy to Avalanche Server

\`\`\`bash
# Configure server credentials
export AVALANCHE_HOST="91.98.16.255"
export AVALANCHE_USER="root"

# Run automated deployment
bash deploy/avalanche/deploy_to_avalanche.sh
\`\`\`

### Manual Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive deployment guide.

### Tor Hidden Service

1. Install Tor:
\`\`\`bash
apt-get install tor
\`\`\`

2. Configure `/etc/tor/torrc`:
\`\`\`
HiddenServiceDir /var/lib/tor/vault/
HiddenServicePort 80 127.0.0.1:8000
\`\`\`

3. Restart Tor and get onion address:
\`\`\`bash
systemctl restart tor
cat /var/lib/tor/vault/hostname
\`\`\`

4. Set `ONION_ADDRESS` in `.env`

### Production Checklist

See [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) for complete deployment checklist including:
- Infrastructure setup
- Security hardening
- Database configuration
- Tor setup
- Monitoring and backups
- Testing procedures

## Development

### Running Tests

\`\`\`bash
pytest
pytest --cov=app tests/
pytest tests/test_auth.py -v
\`\`\`

### Load Testing

\`\`\`bash
locust -f tests/load_test.py --host=http://localhost:8000
\`\`\`

### Code Quality

\`\`\`bash
# Format code
black app/

# Lint code
ruff check app/

# Type checking
mypy app/
\`\`\`

## CLI Management

\`\`\`bash
# Create admin user
python -m app.cli create-admin --username admin --email admin@vault.onion

# Verify vendor
python -m app.cli verify-vendor --user-id 123

# Generate platform keys
python scripts/generate_platform_keys.py

# Database backup
python -m app.cli backup-db --output ./backups/
\`\`\`

## Monitoring

### Prometheus Metrics

Metrics available at `/metrics`:
- Request count and latency
- Active sessions
- Celery task queue depth
- Database connection pool
- PGP operations
- Payment processing

### Health Check

\`\`\`bash
curl http://localhost:8000/health
\`\`\`

## Documentation

For complete technical documentation, architecture details, and implementation guides:
- [PROJECT.md](./PROJECT.md) - Full technical specification
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) - Pre-launch checklist
- [TESTING.md](./TESTING.md) - Testing guide

## Support

### Getting Help

- Review the FAQ in [PROJECT.md](./PROJECT.md)
- Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment issues
- Review API documentation at `/docs`

### Reporting Issues

For security issues, contact: security@vault.onion (PGP required)

For bugs or features, provide:
- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS, etc.)

## License

Open source under MIT License. See LICENSE file for details.

## Acknowledgments

Built with security and privacy as first principles. Designed for secure anonymous marketplace transactions with end-to-end encryption and complete payment privacy via Monero.
