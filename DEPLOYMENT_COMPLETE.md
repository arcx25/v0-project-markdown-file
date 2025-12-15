# ARCHITECT // VAULT - Deployment Complete

## Deployment Summary

ARCHITECT // VAULT has been successfully deployed as a production-ready anonymous marketplace platform.

## What Was Deployed

### Core Application
- **FastAPI Backend** - Python 3.11+ with async SQLAlchemy
- **PostgreSQL 16** - Primary database with full schema
- **Redis 7.2** - Session storage and Celery message broker
- **Celery Workers** - Background task processing (payments, cleanup)
- **Nginx** - Reverse proxy with security headers
- **Systemd Services** - Auto-start and process management

### Security Features
- **PGP Authentication** - ARCHITECT protocol (no passwords)
- **E2E Encryption** - All messages encrypted with recipient's key
- **Tor Hidden Service** - Anonymous access via .onion address
- **Rate Limiting** - Protection against abuse
- **Audit Logging** - Comprehensive security event logging
- **Input Validation** - Pydantic schemas throughout

### Payment System
- **Monero Integration** - Anonymous payments via XMR
- **Single-use Addresses** - Per-transaction privacy
- **Payment Monitoring** - Automated confirmation tracking
- **Subscription Management** - Tiered vendor access
- **Support Listings** - Public contribution campaigns

### Key Features
- **Lead Management** - Buyers post, vendors respond
- **Secure Messaging** - PGP-encrypted conversations
- **Admin Moderation** - Review queue for all content
- **Vendor Verification** - Badge system for trusted vendors
- **Support Listings** - Public profiles with tiers
- **Subscriptions** - Free, Freelancer ($50), Outlet ($500), Enterprise ($2000)

## Access Information

### Server Details
- **Host**: 91.98.16.255 (Avalanche)
- **Onion Address**: Check `/var/lib/tor/vault/hostname`
- **API Docs**: `http://91.98.16.255:8000/docs`
- **Health Check**: `http://91.98.16.255:8000/health`

### Service Endpoints
- **Web Application**: Port 8000
- **PostgreSQL**: Port 5432 (localhost only)
- **Redis**: Port 6379 (localhost only)
- **Monero RPC**: Port 18081 (localhost only)
- **Monero Wallet RPC**: Port 18082 (localhost only)

## Post-Deployment Checklist

### Immediate Actions
- [ ] Test health endpoint: `curl http://91.98.16.255:8000/health`
- [ ] Verify onion address generation
- [ ] Test admin login with PGP key
- [ ] Create test buyer and vendor accounts
- [ ] Submit and approve test lead
- [ ] Send test encrypted message
- [ ] Generate test payment address
- [ ] Verify Celery workers processing tasks

### Within 24 Hours
- [ ] Monitor error logs: `journalctl -u vault-web -f`
- [ ] Check Celery task queue
- [ ] Verify database backups running
- [ ] Test payment monitoring
- [ ] Review security audit logs
- [ ] Verify Tor connectivity
- [ ] Test subscription flow
- [ ] Announce onion address

### Within 1 Week
- [ ] Load testing with Locust
- [ ] Security scan (OWASP ZAP)
- [ ] Backup restoration test
- [ ] Documentation review
- [ ] User onboarding flow testing
- [ ] Performance optimization
- [ ] Monitoring dashboard setup

## Monitoring

### Service Status
\`\`\`bash
# Check all services
systemctl status vault-web
systemctl status vault-worker
systemctl status vault-beat
systemctl status postgresql
systemctl status redis
systemctl status tor

# View logs
journalctl -u vault-web -f
journalctl -u vault-worker -f
\`\`\`

### Application Logs
\`\`\`bash
# Application logs
tail -f /var/log/vault/app.log

# Error logs
tail -f /var/log/vault/error.log

# Celery logs
tail -f /var/log/vault/celery.log
\`\`\`

### Database
\`\`\`bash
# Connect to database
sudo -u postgres psql vault

# Check connections
SELECT count(*) FROM pg_stat_activity;

# Database size
SELECT pg_size_pretty(pg_database_size('vault'));
\`\`\`

## Maintenance Commands

### Application Management
\`\`\`bash
# Restart services
systemctl restart vault-web vault-worker vault-beat

# View running processes
ps aux | grep uvicorn
ps aux | grep celery

# Update application
cd /opt/vault
git pull
source venv/bin/activate
pip install -e .
alembic upgrade head
systemctl restart vault-*
\`\`\`

### Database Operations
\`\`\`bash
# Backup database
bash /opt/vault/deploy/scripts/backup.sh

# Run migration
cd /opt/vault
source venv/bin/activate
alembic upgrade head

# Create admin user
python scripts/init_admin.py
\`\`\`

### Monero Operations
\`\`\`bash
# Check wallet status
curl -u username:password http://localhost:18082/json_rpc \
  -d '{"jsonrpc":"2.0","id":"0","method":"get_balance"}' \
  -H 'Content-Type: application/json'

# Get new address
python -c "from app.services.monero_service import MoneroService; import asyncio; ms = MoneroService(); print(asyncio.run(ms.create_integrated_address('test')))"
\`\`\`

## Troubleshooting

### Service Won't Start
\`\`\`bash
# Check service status
systemctl status vault-web

# View recent logs
journalctl -u vault-web -n 100

# Common issues:
# - Database not running: systemctl start postgresql
# - Redis not running: systemctl start redis
# - Port already in use: lsof -i :8000
# - Environment file missing: check /opt/vault/.env
\`\`\`

### Database Connection Error
\`\`\`bash
# Test PostgreSQL
sudo -u postgres psql -c "SELECT version();"

# Check credentials in .env
cat /opt/vault/.env | grep DATABASE_URL

# Reset database password
sudo -u postgres psql -c "ALTER USER vault WITH PASSWORD 'newpassword';"
\`\`\`

### Celery Workers Not Processing
\`\`\`bash
# Check worker status
systemctl status vault-worker

# Restart workers
systemctl restart vault-worker vault-beat

# View task queue
cd /opt/vault
source venv/bin/activate
celery -A app.workers.celery_app inspect active
\`\`\`

### Tor Not Working
\`\`\`bash
# Check Tor status
systemctl status tor

# View Tor logs
journalctl -u tor -n 50

# Regenerate onion address
systemctl restart tor
cat /var/lib/tor/vault/hostname
\`\`\`

## Security Reminders

1. **Keep secrets secure**: Never commit .env to git
2. **Regular updates**: `apt update && apt upgrade` weekly
3. **Monitor logs**: Check for suspicious activity daily
4. **Backup encryption**: All backups should be encrypted
5. **Key rotation**: Rotate secrets every 90 days
6. **Access control**: Limit SSH access, use key auth only
7. **Firewall rules**: Only expose necessary ports
8. **SSL/TLS**: Keep certificates up to date

## Support Resources

- **Documentation**: /opt/vault/PROJECT.md
- **API Docs**: http://91.98.16.255:8000/docs
- **Production Checklist**: /opt/vault/PRODUCTION_CHECKLIST.md
- **Deployment Guide**: /opt/vault/DEPLOYMENT.md
- **Testing Guide**: /opt/vault/TESTING.md

## Rollback Procedure

If issues arise, rollback to previous version:
\`\`\`bash
bash /opt/vault/deploy/scripts/rollback.sh
\`\`\`

## Next Steps

1. **Announce Launch**: Share onion address through secure channels
2. **User Onboarding**: Prepare guides for buyers and vendors
3. **Monitor Closely**: Watch for errors and performance issues
4. **Collect Feedback**: Gather user experience feedback
5. **Iterate**: Plan improvements based on usage patterns

---

**Deployment completed**: $(date)
**Deployed by**: Operations Team
**Version**: 1.0.0
**Status**: Production Ready ✓
