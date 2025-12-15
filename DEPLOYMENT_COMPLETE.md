# ARCHITECT - Deployment Complete

## Deployment Summary

ARCHITECT has been successfully deployed as a production-ready anonymous XMR marketplace platform connecting buyers with verified vendors.

## What Was Deployed

### Core Application
- **FastAPI Backend** - Python 3.11+ with async SQLAlchemy ORM
- **PostgreSQL 16** - Primary database with full marketplace schema
- **Redis 7.2** - Session storage, caching, and Celery message broker
- **Celery Workers** - Background task processing (payment monitoring, subscription management, cleanup)
- **Nginx** - Reverse proxy with rate limiting and security headers
- **Systemd Services** - Auto-start configuration and process management

### Security Features
- **PGP Authentication** - ARCHITECT protocol (cryptographic key-based auth, no passwords)
- **E2E Encryption** - All messages encrypted with recipient's PGP public key
- **Tor Hidden Service** - Anonymous access via v3 .onion address
- **Rate Limiting** - Role-based limits (buyer/vendor/admin) with Redis backend
- **Audit Logging** - Comprehensive security event tracking
- **Input Validation** - Strict Pydantic schemas throughout API
- **CSRF Protection** - Token-based protection for all state-changing operations

### Payment System
- **Monero Integration** - Anonymous XMR-only payments
- **Integrated Addresses** - Unique payment IDs per transaction
- **Payment Monitoring** - Automated confirmation tracking via Celery workers
- **Subscription Management** - Tiered vendor access (Free, Professional, Enterprise)
- **Support Listings** - Public vendor profiles with contribution tiers
- **Escrow System** - Multi-signature transaction protection

### Marketplace Features
- **Opportunity Management** - Buyers post needs, vendors submit proposals
- **Secure Messaging** - PGP-encrypted conversations between buyers and vendors
- **Admin Moderation** - Review queue for opportunities, vendors, and listings
- **Vendor Verification** - Badge system for admin-verified trusted vendors
- **Product Listings** - Vendor catalogs with XMR pricing
- **Subscription Tiers**:
  - **Free Tier** - 5 opportunities/month, basic messaging
  - **Professional Tier** - 50 XMR/month, unlimited opportunities, priority support
  - **Enterprise Tier** - 200 XMR/month, featured placement, dedicated account manager

## Access Information

### Server Details
- **Host**: 91.98.16.255 (Avalanche VPS)
- **Onion Address**: Check `/var/lib/tor/architect_vault/hostname`
- **API Documentation**: `http://91.98.16.255:8000/docs`
- **Health Check**: `http://91.98.16.255:8000/health`
- **Metrics**: `http://91.98.16.255:8000/metrics` (admin only)

### Service Endpoints
- **Web Application**: Port 8000 (FastAPI with Jinja2 templates)
- **PostgreSQL**: Port 5432 (localhost only, firewalled)
- **Redis**: Port 6379 (localhost only, firewalled)
- **Monero RPC**: Port 18081 (localhost only)
- **Monero Wallet RPC**: Port 18083 (localhost only)

## Post-Deployment Checklist

### Immediate Actions (First Hour)
- [ ] Test health endpoint: `curl http://91.98.16.255:8000/health`
- [ ] Verify Tor onion address generation: `cat /var/lib/tor/architect_vault/hostname`
- [ ] Create admin account: `python scripts/init_admin.py`
- [ ] Test admin login with PGP key authentication
- [ ] Create test buyer account via registration flow
- [ ] Create test vendor account via registration flow
- [ ] Post test opportunity as buyer
- [ ] Submit proposal as vendor
- [ ] Admin approve opportunity and vendor verification
- [ ] Send test encrypted message between buyer and vendor
- [ ] Generate test Monero payment address
- [ ] Verify Celery workers are processing tasks: `systemctl status vault-worker`

### Within 24 Hours
- [ ] Monitor application logs: `journalctl -u vault-web -f`
- [ ] Monitor worker logs: `journalctl -u vault-worker -f`
- [ ] Check Celery task queue depth in Redis
- [ ] Verify database connection pooling working correctly
- [ ] Test payment monitoring worker with real XMR transaction
- [ ] Review security audit logs for any anomalies
- [ ] Verify Tor connectivity from external network
- [ ] Test subscription upgrade flow (Free → Professional)
- [ ] Create test support listing as vendor
- [ ] Verify rate limiting is active and blocking excessive requests
- [ ] Configure database backup schedule
- [ ] Set up monitoring alerts (Prometheus/Grafana optional)

### Within 1 Week
- [ ] Load testing with realistic traffic patterns
- [ ] Security penetration testing (OWASP Top 10)
- [ ] Backup restoration test from production data
- [ ] Performance optimization based on real usage metrics
- [ ] User onboarding flow testing with real users
- [ ] Documentation review and updates
- [ ] Monitoring dashboard setup and alert configuration
- [ ] Disaster recovery plan documentation
- [ ] SSL/TLS certificate setup for clearnet access (optional)
- [ ] Rate limit tuning based on actual usage patterns

## Monitoring

### Service Status Checks
\`\`\`bash
# Check all ARCHITECT services
systemctl status vault-web          # FastAPI application
systemctl status vault-worker       # Celery worker
systemctl status vault-beat         # Celery beat scheduler
systemctl status postgresql         # Database
systemctl status redis              # Cache/queue
systemctl status tor                # Anonymity network
systemctl status nginx              # Reverse proxy

# View real-time logs
journalctl -u vault-web -f          # Application logs
journalctl -u vault-worker -f       # Background worker logs
journalctl -u tor -f                # Tor service logs
\`\`\`

### Application Logs
\`\`\`bash
# Application logs (structured JSON)
tail -f /opt/architect-vault/logs/app.log

# Error logs only
tail -f /opt/architect-vault/logs/error.log | grep ERROR

# Celery task logs
tail -f /opt/architect-vault/logs/celery.log

# Security audit logs
tail -f /opt/architect-vault/logs/audit.log
\`\`\`

### Database Monitoring
\`\`\`bash
# Connect to PostgreSQL
sudo -u postgres psql architect_vault

# Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'architect_vault';

# Database size
SELECT pg_size_pretty(pg_database_size('architect_vault'));

# Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Long-running queries
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '1 minute';
\`\`\`

### Redis Monitoring
\`\`\`bash
# Connect to Redis CLI
redis-cli

# Check memory usage
INFO memory

# Check keyspace
INFO keyspace

# Monitor commands in real-time
MONITOR
\`\`\`

## Maintenance Commands

### Application Management
\`\`\`bash
# Restart all ARCHITECT services
systemctl restart vault-web vault-worker vault-beat

# View running processes
ps aux | grep uvicorn
ps aux | grep celery

# Update application code
cd /opt/architect-vault
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart vault-web vault-worker vault-beat

# View environment configuration
cat /opt/architect-vault/.env | grep -v "SECRET\|PASSWORD\|KEY"
\`\`\`

### Database Operations
\`\`\`bash
# Backup database
sudo -u postgres pg_dump architect_vault | gzip > /opt/backups/architect_vault_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore database
gunzip -c /opt/backups/architect_vault_YYYYMMDD_HHMMSS.sql.gz | sudo -u postgres psql architect_vault

# Run new migrations
cd /opt/architect-vault
source venv/bin/activate
alembic upgrade head

# Create database backup schedule (cron)
echo "0 2 * * * postgres pg_dump architect_vault | gzip > /opt/backups/architect_vault_\$(date +\\%Y\\%m\\%d).sql.gz" | sudo crontab -
\`\`\`

### Monero Operations
\`\`\`bash
# Check wallet balance
curl -u username:password http://localhost:18083/json_rpc \
  -d '{"jsonrpc":"2.0","id":"0","method":"get_balance"}' \
  -H 'Content-Type: application/json'

# Generate new integrated address
cd /opt/architect-vault
source venv/bin/activate
python -c "
from app.services.monero_service import MoneroService
import asyncio
ms = MoneroService()
result = asyncio.run(ms.create_integrated_address('test_payment'))
print(result)
"

# Check Monero daemon sync status
curl http://localhost:18081/json_rpc \
  -d '{"jsonrpc":"2.0","id":"0","method":"get_info"}' \
  -H 'Content-Type: application/json'
\`\`\`

### User Management
\`\`\`bash
cd /opt/architect-vault
source venv/bin/activate

# Create admin user
python scripts/init_admin.py

# Verify vendor
python -m app.cli verify-vendor --user-id 123

# List all users
python -m app.cli list-users

# Ban user
python -m app.cli ban-user --user-id 456 --reason "spam"
\`\`\`

## Troubleshooting

### Service Won't Start
\`\`\`bash
# Check service status and logs
systemctl status vault-web
journalctl -u vault-web -n 100 --no-pager

# Common issues and fixes:
# 1. Database not running
systemctl start postgresql
systemctl status postgresql

# 2. Redis not running
systemctl start redis
systemctl status redis

# 3. Port already in use
lsof -i :8000
kill -9 <PID>

# 4. Environment file missing or incorrect
ls -la /opt/architect-vault/.env
cat /opt/architect-vault/.env

# 5. Python dependencies missing
cd /opt/architect-vault
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### Database Connection Errors
\`\`\`bash
# Test PostgreSQL connectivity
sudo -u postgres psql -c "SELECT version();"

# Check database credentials
cat /opt/architect-vault/.env | grep DATABASE_URL

# Reset database password
sudo -u postgres psql -c "ALTER USER architect WITH PASSWORD 'new_secure_password';"

# Update .env with new password
nano /opt/architect-vault/.env

# Restart application
systemctl restart vault-web
\`\`\`

### Celery Workers Not Processing Tasks
\`\`\`bash
# Check worker status
systemctl status vault-worker
journalctl -u vault-worker -n 50

# Restart workers
systemctl restart vault-worker vault-beat

# Inspect task queue
cd /opt/architect-vault
source venv/bin/activate
celery -A app.workers.celery_app inspect active
celery -A app.workers.celery_app inspect scheduled

# Clear failed tasks
celery -A app.workers.celery_app purge
\`\`\`

### Tor Hidden Service Not Working
\`\`\`bash
# Check Tor status
systemctl status tor
journalctl -u tor -n 50

# Verify Tor configuration
cat /etc/tor/torrc | grep -A 5 "HiddenService"

# Check hidden service directory permissions
ls -la /var/lib/tor/architect_vault/

# Regenerate onion address
systemctl stop tor
rm -rf /var/lib/tor/architect_vault/*
systemctl start tor
sleep 5
cat /var/lib/tor/architect_vault/hostname
\`\`\`

### High Memory Usage
\`\`\`bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -n 10

# Restart memory-intensive services
systemctl restart vault-worker
systemctl restart vault-web

# Check for memory leaks
journalctl -u vault-web | grep "MemoryError\|OutOfMemory"

# Increase swap if needed
dd if=/dev/zero of=/swapfile bs=1G count=4
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
\`\`\`

### Payment Monitoring Issues
\`\`\`bash
# Check Monero wallet RPC connectivity
curl http://localhost:18083/json_rpc \
  -d '{"jsonrpc":"2.0","id":"0","method":"get_height"}' \
  -H 'Content-Type: application/json'

# Check payment monitoring worker logs
journalctl -u vault-worker -f | grep "payment"

# Manually trigger payment check
cd /opt/architect-vault
source venv/bin/activate
python -c "
from app.workers.payment_monitor import check_pending_payments
import asyncio
asyncio.run(check_pending_payments())
"
\`\`\`

## Security Reminders

### Critical Security Practices
1. **Secrets Management**: Never commit `.env` to version control
2. **Regular Updates**: `apt update && apt upgrade` weekly
3. **Log Monitoring**: Check audit logs for suspicious activity daily
4. **Backup Encryption**: Encrypt all database backups with GPG
5. **Key Rotation**: Rotate API keys and secrets every 90 days
6. **SSH Hardening**: Key-based auth only, disable password login
7. **Firewall Configuration**: Only expose port 80/443, block everything else
8. **Tor Security**: Keep Tor updated, monitor for relay attacks

### Security Checklist
\`\`\`bash
# Verify firewall rules
ufw status verbose

# Check for failed login attempts
journalctl _SYSTEMD_UNIT=sshd.service | grep "Failed password"

# Review security audit logs
tail -f /opt/architect-vault/logs/audit.log | grep "SECURITY"

# Check for unauthorized sudo usage
journalctl _COMM=sudo

# Verify PGP key integrity
gpg --list-keys --keyid-format LONG
\`\`\`

## Performance Optimization

### Database Tuning
\`\`\`bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/16/main/postgresql.conf

# Recommended settings for 4GB RAM server:
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 32MB
max_worker_processes = 4
max_parallel_workers_per_gather = 2

# Restart PostgreSQL
systemctl restart postgresql
\`\`\`

### Nginx Optimization
\`\`\`bash
# Edit Nginx config
sudo nano /etc/nginx/nginx.conf

# Recommended settings:
worker_processes auto;
worker_connections 2048;
keepalive_timeout 65;
client_max_body_size 25M;
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# Reload Nginx
nginx -t && systemctl reload nginx
\`\`\`

### Redis Configuration
\`\`\`bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Recommended settings:
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# Restart Redis
systemctl restart redis
\`\`\`

## Support Resources

- **Project Documentation**: `/opt/architect-vault/PROJECT.md`
- **API Documentation**: `http://91.98.16.255:8000/docs`
- **Production Checklist**: `/opt/architect-vault/PRODUCTION_CHECKLIST.md`
- **Deployment Guide**: `/opt/architect-vault/DEPLOYMENT.md`
- **Testing Guide**: `/opt/architect-vault/TESTING.md`
- **System Verification**: `/opt/architect-vault/SYSTEM_VERIFICATION.md`

## Rollback Procedure

If critical issues arise, rollback to previous version:
\`\`\`bash
# Automated rollback script
bash /opt/architect-vault/deploy/avalanche/rollback.sh

# Manual rollback steps:
cd /opt/architect-vault
git log --oneline -10  # Find previous commit hash
git checkout <previous_commit_hash>
source venv/bin/activate
pip install -r requirements.txt
alembic downgrade -1  # Roll back one migration
systemctl restart vault-web vault-worker vault-beat
\`\`\`

## Next Steps

### Launch Preparation
1. **Announce Launch**: Share .onion address through secure channels (PGP-encrypted)
2. **User Onboarding**: Prepare buyer and vendor registration guides
3. **Monitor Closely**: Watch logs for errors, performance issues, security events
4. **Collect Feedback**: Gather user experience feedback from early adopters
5. **Iterate**: Plan improvements based on real usage patterns

### Growth Strategy
1. **Vendor Recruitment**: Onboard verified vendors across multiple categories
2. **Marketing**: Promote platform on darknet forums (maintain OPSEC)
3. **Feature Development**: Add requested features based on user feedback
4. **Security Audits**: Regular penetration testing and code reviews
5. **Community Building**: Foster active buyer/vendor community

---

**Deployment Completed**: Production-ready buyer/vendor XMR marketplace  
**Platform**: ARCHITECT  
**Version**: 1.0.0  
**Status**: ✓ Live and operational  
**Onion Address**: Check `/var/lib/tor/architect_vault/hostname`
