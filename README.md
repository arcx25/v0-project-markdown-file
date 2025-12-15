# ARCHITECT // VAULT

Secure platform connecting whistleblowers with verified journalists through PGP-authenticated, end-to-end encrypted channels.

## Overview

ARCHITECT // VAULT is a production-ready whistleblowing platform featuring:

- **PGP-based authentication** - No passwords, cryptographic proof of identity
- **End-to-end encryption** - Messages encrypted with recipient's public key
- **Tor integration** - Hidden service for maximum anonymity
- **Anonymous payments** - Monero-based donations for whistleblower support
- **Lead management** - Sources submit leads, journalists express interest
- **Secure messaging** - Encrypted conversations between matched parties
- **Admin moderation** - Review system for leads, journalists, and listings

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- Redis 7.2
- GnuPG 2.4+
- Monero wallet RPC (optional, for payments)
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

### Project Structure

\`\`\`
vault/
├── app/
│   ├── api/              # REST API endpoints
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   ├── workers/          # Background tasks
│   ├── web/              # Web frontend routes
│   ├── templates/        # HTML templates
│   ├── static/           # CSS, JS, assets
│   ├── config.py         # Configuration
│   ├── database.py       # Database setup
│   └── main.py           # Application entry
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
- `POST /api/auth/register/verify` - Complete registration
- `POST /api/auth/login/challenge` - Initiate login
- `POST /api/auth/login/verify` - Complete login

**Leads**
- `GET /api/leads` - Browse active leads (journalist)
- `POST /api/leads` - Create lead (source)
- `POST /api/leads/{id}/interest` - Express interest (journalist)
- `POST /api/leads/{id}/accept/{journalist_id}` - Accept journalist (source)

**Messages**
- `GET /api/conversations` - List conversations
- `GET /api/conversations/{id}/messages` - Get messages
- `POST /api/conversations/{id}/messages` - Send message

**Support Listings**
- `GET /api/listings` - Browse listings (public)
- `POST /api/listings` - Create listing (source)
- `POST /api/listings/{slug}/contribute` - Initiate contribution

**Admin**
- `GET /api/admin/leads/pending` - Pending leads
- `POST /api/admin/leads/{id}/approve` - Approve lead
- `GET /api/admin/journalists/pending` - Pending verifications
- `POST /api/admin/journalists/{id}/verify` - Verify journalist

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

## Deployment

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

- [ ] Set strong `SECRET_KEY` (64+ characters)
- [ ] Configure PostgreSQL with strong password
- [ ] Set up Tor hidden service
- [ ] Configure Monero wallet RPC
- [ ] Enable HTTPS/TLS
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Review security headers
- [ ] Test PGP key import/verification
- [ ] Initialize admin user

## Development

### Running Tests

\`\`\`bash
pytest
pytest --cov=app tests/
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

## Documentation

For complete technical documentation, architecture details, and implementation guides, see [PROJECT.md](./PROJECT.md).

## Support

### Getting Help

- Read the FAQ in [PROJECT.md](./PROJECT.md)
- Check the [Security](./SECURITY.md) documentation
- Review API documentation at `/docs`

### Reporting Issues

For security issues, contact: security@vault.onion (PGP required)

For bugs or features, open an issue with:
- Description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details

## License

Open source under MIT License. See LICENSE file for details.

## Acknowledgments

Built with security and privacy as first principles. Inspired by the need for secure journalist-source communication in the digital age.
