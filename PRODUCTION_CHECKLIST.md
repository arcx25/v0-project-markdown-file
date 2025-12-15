# ARCHITECT // VAULT - Production Deployment Checklist

## Pre-Deployment Security

### [ ] Cryptographic Keys
- [ ] Generate platform PGP keypair with Ed25519 algorithm
- [ ] Store private key securely (encrypted filesystem, HSM, or vault)
- [ ] Back up private key to offline secure storage
- [ ] Set strong passphrase for private key (min 20 characters)
- [ ] Document key fingerprint and store separately

### [ ] Environment Variables
- [ ] All secrets use cryptographically secure random generation
- [ ] No default/example values in production `.env`
- [ ] DATABASE_URL uses strong password (min 32 characters)
- [ ] REDIS_PASSWORD uses strong password
- [ ] SESSION_SECRET_KEY is unique per deployment
- [ ] MONERO_WALLET_PASSWORD is strong and unique

### [ ] Database Security
- [ ] PostgreSQL configured for SSL/TLS connections only
- [ ] Database user has minimal required permissions
- [ ] Connection pooling limits configured
- [ ] Regular backup schedule configured
- [ ] Point-in-time recovery enabled

### [ ] Server Hardening
- [ ] SSH key-only authentication (no passwords)
- [ ] Firewall configured (only ports 22, 80, 443, Tor open)
- [ ] Fail2Ban installed and monitoring auth attempts
- [ ] Automatic security updates enabled
- [ ] SELinux/AppArmor enforcing mode
- [ ] Root login disabled

## Application Configuration

### [ ] Tor Integration
- [ ] Tor hidden service configured in `/etc/tor/torrc`
- [ ] Onion address documented
- [ ] Circuit isolation enabled
- [ ] Tor control authentication configured

### [ ] Rate Limiting
- [ ] Redis rate limiting functional
- [ ] Auth attempt limits tested
- [ ] Registration rate limits configured
- [ ] API rate limits per-user tested

### [ ] Monitoring
- [ ] Prometheus metrics exporter running
- [ ] Grafana dashboards configured
- [ ] Alert rules for critical errors
- [ ] Log aggregation configured
- [ ] Sentry error tracking active

## Monero Integration

### [ ] Node Setup
- [ ] Monero daemon synchronized with network
- [ ] RPC authentication configured
- [ ] Node running as systemd service
- [ ] Blockchain storage sufficient (200+ GB)

### [ ] Wallet Configuration
- [ ] Wallet RPC running and authenticated
- [ ] Wallet passphrase set and documented
- [ ] View key backed up securely
- [ ] Spend key in cold storage
- [ ] Test transactions confirmed

## Testing

### [ ] Security Testing
- [ ] PGP key validation tested (accept Ed25519, reject DSA)
- [ ] Challenge-response authentication flow tested
- [ ] Session binding to Tor circuits tested
- [ ] Rate limiting triggers tested
- [ ] SQL injection protection verified
- [ ] XSS protection verified

### [ ] Functional Testing
- [ ] User registration complete flow
- [ ] User login complete flow
- [ ] Lead creation and browsing
- [ ] Vendor-buyer messaging
- [ ] Monero payment detection
- [ ] Support listing contributions

### [ ] Load Testing
- [ ] Concurrent user load tested (target: 1000 users)
- [ ] Database query performance profiled
- [ ] Redis cache hit rates measured
- [ ] API response times under load < 200ms

## Deployment

### [ ] Initial Deployment
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Create admin user: `python scripts/init_admin.py`
- [ ] Generate platform keys: `python scripts/generate_platform_keys.py`
- [ ] Start services: `systemctl start vault-web vault-worker vault-beat`
- [ ] Verify hidden service accessible

### [ ] Post-Deployment
- [ ] Health check endpoint returns 200: `/health`
- [ ] Metrics endpoint accessible: `/metrics`
- [ ] Admin dashboard accessible
- [ ] Test user registration
- [ ] Monitor logs for errors

## Ongoing Operations

### [ ] Backup Procedures
- [ ] Daily PostgreSQL backups to encrypted remote storage
- [ ] Weekly full system snapshots
- [ ] Monthly disaster recovery drill
- [ ] Backup restoration tested quarterly

### [ ] Monitoring
- [ ] Daily review of error logs
- [ ] Weekly security audit log review
- [ ] Monthly dependency vulnerability scan
- [ ] Quarterly penetration testing

### [ ] Maintenance
- [ ] Security updates applied within 48 hours
- [ ] Database vacuum/analyze scheduled
- [ ] Redis persistence verified
- [ ] Monero node kept synchronized

## Emergency Procedures

### [ ] Incident Response
- [ ] Security incident response plan documented
- [ ] Contact information for team members
- [ ] Backup admin access method established
- [ ] Service restoration runbook created

### [ ] Known Issues
- [ ] Document any known limitations
- [ ] Track technical debt items
- [ ] Plan for scaling bottlenecks

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Onion Address:** _________________

**Admin PGP Fingerprint:** _________________

**Review Date:** _________________
