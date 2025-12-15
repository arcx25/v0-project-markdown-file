# ARCHITECT // VAULT - Production Deployment Checklist

## Pre-Deployment

### Infrastructure
- [ ] Debian 12 server provisioned (minimum 4GB RAM, 50GB SSD)
- [ ] Server hardened (firewall, fail2ban, automatic updates)
- [ ] SSH key-based authentication configured
- [ ] Root login disabled
- [ ] Non-root user created with sudo access
- [ ] Hostname set appropriately

### Dependencies
- [ ] Python 3.11+ installed
- [ ] PostgreSQL 16 installed and running
- [ ] Redis 7.2 installed and running
- [ ] GnuPG 2.4+ installed
- [ ] Tor installed and configured
- [ ] Nginx installed (for reverse proxy)
- [ ] Monero node synced (if self-hosting)
- [ ] Monero wallet RPC configured

### Security
- [ ] Firewall configured (UFW or iptables)
  - Allow: 22 (SSH), 80 (HTTP), 443 (HTTPS)
  - Block: All other inbound
- [ ] Fail2ban configured for SSH
- [ ] Automatic security updates enabled
- [ ] LUKS full-disk encryption (recommended)
- [ ] Secure backup location configured

## Configuration

### Environment Variables
- [ ] `.env` file created from `.env.example`
- [ ] `SECRET_KEY` generated (64+ characters)
  \`\`\`bash
  openssl rand -hex 32
  \`\`\`
- [ ] `DATABASE_URL` configured with strong password
- [ ] `REDIS_URL` configured
- [ ] `GPG_HOME_DIR` set and directory created
- [ ] `MONERO_WALLET_RPC_URL` configured
- [ ] `MONERO_WALLET_RPC_USERNAME` set
- [ ] `MONERO_WALLET_RPC_PASSWORD` set (strong password)
- [ ] `ADMIN_GPG_FINGERPRINT` set
- [ ] `PLATFORM_EMAIL` configured
- [ ] `LOG_LEVEL` set (INFO for production)

### Database
- [ ] PostgreSQL database created
- [ ] Database user created with strong password
- [ ] Database user permissions granted
- [ ] Connection tested from application
- [ ] Alembic migrations run: `alembic upgrade head`
- [ ] Database backups configured (daily minimum)

### Tor Configuration
- [ ] Tor hidden service directory created
- [ ] `/etc/tor/torrc` configured:
  \`\`\`
  HiddenServiceDir /var/lib/tor/vault/
  HiddenServicePort 80 127.0.0.1:8000
  \`\`\`
- [ ] Tor restarted: `systemctl restart tor`
- [ ] Onion address saved: `cat /var/lib/tor/vault/hostname`
- [ ] `ONION_ADDRESS` set in `.env`
- [ ] Tor connectivity tested

### PGP Keys
- [ ] Platform PGP key generated:
  \`\`\`bash
  python scripts/generate_platform_keys.py
  \`\`\`
- [ ] Platform key backed up securely (offline storage)
- [ ] Admin PGP key imported
- [ ] Admin key verified and trusted
- [ ] Key expiration dates noted

### Nginx
- [ ] Nginx configuration created (`/etc/nginx/sites-available/vault`)
- [ ] Configuration symlinked to sites-enabled
- [ ] SSL/TLS certificates obtained (Let's Encrypt)
- [ ] Security headers configured
- [ ] Rate limiting configured
- [ ] Nginx configuration tested: `nginx -t`
- [ ] Nginx reloaded: `systemctl reload nginx`

### Systemd Services
- [ ] vault-web.service copied to `/etc/systemd/system/`
- [ ] vault-worker.service copied to `/etc/systemd/system/`
- [ ] vault-beat.service copied to `/etc/systemd/system/`
- [ ] Service files configured with correct paths
- [ ] Services enabled: `systemctl enable vault-*`
- [ ] Services started: `systemctl start vault-*`
- [ ] Service status verified: `systemctl status vault-*`

## Application Setup

### Initial Data
- [ ] Admin user created: `python scripts/init_admin.py`
- [ ] Admin login tested via API
- [ ] Admin access to dashboard verified
- [ ] Sample categories/tags created (if needed)

### Monero Integration
- [ ] Monero wallet RPC connectivity tested
- [ ] Wallet unlocked and synced
- [ ] Test payment address generated
- [ ] Test payment monitored successfully
- [ ] Wallet backup created

### Testing
- [ ] Health check endpoint responding: `/health`
- [ ] API documentation accessible: `/docs`
- [ ] Authentication flow tested (register + login)
- [ ] PGP signature verification working
- [ ] Lead creation and approval tested
- [ ] Messaging encryption verified
- [ ] Payment address generation working
- [ ] Background workers processing tasks
- [ ] Email notifications sending (if configured)

## Security Audit

### Application Security
- [ ] All default passwords changed
- [ ] Rate limiting tested and working
- [ ] CSRF protection enabled
- [ ] XSS protection headers set
- [ ] SQL injection prevention verified (ORM usage)
- [ ] Input validation working (Pydantic schemas)
- [ ] File upload restrictions enforced
- [ ] Session management secure (circuit binding)
- [ ] Logout functionality working

### Infrastructure Security
- [ ] Unnecessary services disabled
- [ ] Port scan performed (only expected ports open)
- [ ] SSL/TLS configuration rated A+ (ssllabs.com)
- [ ] Security headers verified (securityheaders.com)
- [ ] Fail2ban logs checked for attacks
- [ ] Log files reviewed for anomalies
- [ ] Backup restoration tested

### Privacy Verification
- [ ] IP addresses not logged in application
- [ ] Tor circuit binding working
- [ ] Message encryption verified (cannot read plaintext)
- [ ] Payment privacy confirmed (single-use addresses)
- [ ] Metadata minimization verified
- [ ] Analytics/tracking disabled

## Monitoring & Maintenance

### Logging
- [ ] Application logs configured
- [ ] Log rotation enabled (logrotate)
- [ ] Error alerting configured (email/Slack)
- [ ] Audit logs reviewed
- [ ] Log retention policy defined

### Monitoring
- [ ] Prometheus metrics endpoint: `/metrics`
- [ ] Grafana dashboards configured (optional)
- [ ] Uptime monitoring configured (UptimeRobot, etc.)
- [ ] Disk space monitoring enabled
- [ ] Database performance monitoring
- [ ] Celery task monitoring

### Backups
- [ ] Database backup script tested
- [ ] Backup restoration tested
- [ ] Backup encryption enabled
- [ ] Off-site backup location configured
- [ ] Backup retention policy defined (30 days minimum)
- [ ] Automated backup schedule configured (daily)
- [ ] PGP keys backed up separately (offline)
- [ ] .env file backed up securely

### Maintenance Procedures
- [ ] Update procedure documented
- [ ] Rollback procedure documented and tested
- [ ] Incident response plan created
- [ ] Admin contact information documented
- [ ] On-call rotation defined (if team)

## Go-Live

### Pre-Launch
- [ ] All checklist items completed
- [ ] Full system test performed
- [ ] Load testing completed (optional but recommended)
- [ ] Security scan performed (OWASP ZAP, etc.)
- [ ] Backup verified within last 24 hours
- [ ] Emergency contacts notified
- [ ] Launch announcement prepared

### Launch
- [ ] DNS records updated (if using clearnet)
- [ ] Onion address announced
- [ ] Admin monitoring dashboard
- [ ] Ready to respond to issues
- [ ] First users registered and tested

### Post-Launch
- [ ] Monitor error logs for first 24 hours
- [ ] Verify backup completion after launch
- [ ] Check Celery task queue processing
- [ ] Verify Monero payments processing
- [ ] Review system performance metrics
- [ ] Collect user feedback
- [ ] Plan first maintenance window

## Ongoing Operations

### Daily
- [ ] Review error logs
- [ ] Check system resource usage
- [ ] Verify backup completion
- [ ] Monitor Celery queue depth

### Weekly
- [ ] Review security alerts
- [ ] Check failed login attempts
- [ ] Review admin actions log
- [ ] Verify payment processing
- [ ] Check disk space usage

### Monthly
- [ ] Update dependencies (security patches)
- [ ] Review user growth and metrics
- [ ] Test backup restoration
- [ ] Security audit of new features
- [ ] Review and rotate logs

### Quarterly
- [ ] Full security audit
- [ ] Load testing
- [ ] Disaster recovery drill
- [ ] Review and update documentation
- [ ] Renew SSL/TLS certificates (if not auto-renewed)

## Emergency Procedures

### Service Outage
1. Check systemd service status
2. Review error logs
3. Restart affected services
4. Notify users if extended downtime
5. Document incident and resolution

### Security Incident
1. Isolate affected systems
2. Preserve logs and evidence
3. Notify administrators immediately
4. Follow incident response plan
5. Notify users if data compromised

### Data Loss
1. Stop all write operations
2. Restore from most recent backup
3. Verify data integrity
4. Document lost data (if any)
5. Review backup procedures

## Compliance

### GDPR (if applicable)
- [ ] Privacy policy published
- [ ] Data retention policy defined
- [ ] User data export functionality
- [ ] User account deletion functionality
- [ ] Data processing agreement (DPA) prepared
- [ ] Cookie consent implemented (if using clearnet)

### Legal
- [ ] Terms of service published
- [ ] Acceptable use policy defined
- [ ] Content moderation policy defined
- [ ] Legal counsel consulted (recommended)
- [ ] Jurisdiction and governing law specified

## Documentation

- [ ] Admin documentation complete
- [ ] User guides published
- [ ] API documentation current
- [ ] Runbooks created for common tasks
- [ ] Architecture diagrams current
- [ ] Contact information for support

## Sign-Off

**Deployment Lead**: _________________ Date: _______

**Security Reviewer**: _________________ Date: _______

**System Administrator**: _________________ Date: _______

---

**Notes**: This checklist should be customized based on your specific deployment environment and requirements. Always test in a staging environment before production deployment.
