# ARCHITECT // VAULT - Deployment Guide

Complete deployment guide for production deployment of the ARCHITECT // VAULT platform on Debian 12 with Tor hidden service support.

## Prerequisites

- Fresh Debian 12 server (minimum 2GB RAM, 20GB storage)
- Root access to the server
- Basic understanding of Linux system administration
- SSH key authentication configured

## Quick Start

### 1. Initial Server Setup

Run the automated setup script on your fresh server:

\`\`\`bash
# On your server as root
cd /opt
git clone <your-repo-url> vault
cd vault
chmod +x deploy/scripts/setup_server.sh
./deploy/scripts/setup_server.sh
\`\`\`

This script will:
- Update system packages
- Install all dependencies (Python, PostgreSQL, Redis, Tor, Nginx)
- Configure firewall (UFW)
- Set up Fail2Ban for security
- Create application user and directories
- Generate Tor hidden service
- Configure systemd services

### 2. Configure Deployment

Copy the deployment configuration template:

\`\`\`bash
cp deploy/config/deploy.conf.template deploy/config/deploy.conf
\`\`\`

Edit `deploy/config/deploy.conf` and fill in your values. The template includes secure password generation commands.

**IMPORTANT:** Never commit `deploy.conf` to version control!

### 3. Generate Platform Keys

Generate the platform's PGP keypair:

\`\`\`bash
python3 scripts/generate_platform_keys.py
\`\`\`

Save the output passphrase and key paths to your `.env` file.

### 4. Deploy Application

From your local machine:

\`\`\`bash
cd deploy/scripts
./deploy.sh
\`\`\`

This will:
- Upload application code
- Install Python dependencies
- Run database migrations
- Configure environment variables
- Start all services

### 5. Create Admin User

\`\`\`bash
# On the server
cd /opt/vault
source venv/bin/activate
python scripts/init_admin.py
\`\`\`

Follow the prompts to create your first admin account.

## Architecture

### Services

The platform consists of several services:

1. **vault-web** - FastAPI application server
2. **vault-worker** - Celery background workers
3. **vault-beat** - Celery task scheduler
4. **postgresql** - Database
5. **redis** - Cache and task queue
6. **tor** - Hidden service
7. **nginx** - Reverse proxy
8. **monero** - Monero node and wallet RPC (optional)

### Network Layout

\`\`\`
Internet/Tor Network
        ↓
    Tor Daemon
        ↓
    Nginx (Port 80)
        ↓
FastAPI App (Port 8000)
        ↓
    PostgreSQL / Redis
\`\`\`

## Security Configuration

### Firewall Rules

The setup script configures UFW with:
- SSH (port 22)
- HTTP/HTTPS (ports 80, 443)
- Monero P2P (port 18080, optional)
- All other ports blocked

### Fail2Ban

Configured to protect:
- SSH (3 failures = 24h ban)
- Nginx auth (3 failures = 1h ban)
- Nginx rate limit violations

### Tor Configuration

- Hidden service v3 (56-character onion address)
- DoS protection enabled
- SafeLogging enabled
- Performance optimizations

### Database Security

- Local connections only
- SCRAM-SHA-256 authentication
- Encrypted connections
- Regular automated backups

## Environment Variables

Required environment variables (set in `/etc/vault/environment`):

\`\`\`bash
# Application
SECRET_KEY=<64-char-hex-string>
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://vault:PASSWORD@localhost/vault

# Redis
REDIS_URL=redis://:PASSWORD@localhost:6379/0

# PGP
PGP_PRIVATE_KEY_PATH=/var/lib/vault/gnupg/platform_private.asc
PGP_PUBLIC_KEY_PATH=/var/lib/vault/gnupg/platform_public.asc
PGP_PASSPHRASE=<secure-passphrase>

# Monero
MONERO_WALLET_RPC_URL=http://localhost:18083/json_rpc
MONERO_RPC_USER=vault_rpc
MONERO_RPC_PASSWORD=<secure-password>

# Security
SESSION_TIMEOUT=3600
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=900
\`\`\`

## Monitoring

### Service Status

Check all services:

\`\`\`bash
systemctl status vault-web
systemctl status vault-worker
systemctl status vault-beat
systemctl status postgresql
systemctl status redis-server
systemctl status tor
systemctl status nginx
\`\`\`

### Logs

View application logs:

\`\`\`bash
journalctl -u vault-web -f
journalctl -u vault-worker -f
journalctl -u vault-beat -f
\`\`\`

Nginx logs:

\`\`\`bash
tail -f /var/log/nginx/vault_access.log
tail -f /var/log/nginx/vault_error.log
\`\`\`

### Health Checks

The application exposes a health endpoint:

\`\`\`bash
curl http://localhost:8000/health
\`\`\`

## Backup & Recovery

### Automated Backups

The platform includes automated backup scripts:

\`\`\`bash
/opt/vault/deploy/scripts/backup.sh
\`\`\`

This backs up:
- PostgreSQL database
- PGP keys
- Application configuration
- Upload files

Backups are stored in `/var/lib/vault/backups/`

### Manual Backup

\`\`\`bash
# Database
sudo -u postgres pg_dump vault > vault_backup.sql

# Keys
tar czf keys_backup.tar.gz /var/lib/vault/gnupg/

# Uploads
tar czf uploads_backup.tar.gz /var/lib/vault/uploads/
\`\`\`

### Restore

\`\`\`bash
# Database
sudo -u postgres psql vault < vault_backup.sql

# Keys
tar xzf keys_backup.tar.gz -C /

# Uploads
tar xzf uploads_backup.tar.gz -C /
\`\`\`

## Maintenance

### Update Application

\`\`\`bash
cd /opt/vault
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart vault-web vault-worker vault-beat
\`\`\`

### Database Migrations

\`\`\`bash
cd /opt/vault
source venv/bin/activate
alembic revision --autogenerate -m "description"
alembic upgrade head
\`\`\`

### Clear Redis Cache

\`\`\`bash
redis-cli -a PASSWORD FLUSHALL
\`\`\`

## Troubleshooting

### Application Won't Start

1. Check logs: `journalctl -u vault-web -n 100`
2. Verify database connection: `psql -U vault -d vault -h localhost`
3. Check environment file: `/etc/vault/environment`
4. Verify file permissions: `ls -la /opt/vault`

### Tor Hidden Service Not Working

1. Check Tor status: `systemctl status tor`
2. View Tor logs: `journalctl -u tor -f`
3. Verify hidden service: `cat /var/lib/tor/vault/hostname`
4. Check Nginx configuration: `nginx -t`

### Database Connection Issues

1. Check PostgreSQL status: `systemctl status postgresql`
2. Test connection: `sudo -u postgres psql`
3. Review pg_hba.conf: `/etc/postgresql/*/main/pg_hba.conf`
4. Check database logs: `tail -f /var/log/postgresql/*.log`

### Memory Issues

If experiencing memory issues:

1. Reduce worker processes in systemd service files
2. Configure swap space
3. Optimize PostgreSQL shared_buffers
4. Enable Redis memory limits

## Security Best Practices

1. **Regular Updates**: Enable unattended-upgrades (configured by setup script)
2. **SSH Hardening**: Disable password auth, use key-based only
3. **Firewall**: Only expose required ports
4. **Monitoring**: Set up log monitoring and alerting
5. **Backups**: Automated daily backups to secure location
6. **Key Rotation**: Rotate session secrets periodically
7. **Audit Logs**: Review audit logs regularly
8. **Rate Limiting**: Nginx rate limits configured
9. **DoS Protection**: Tor DoS protection enabled
10. **Fail2Ban**: Monitor ban lists regularly

## Performance Tuning

### PostgreSQL

Edit `/etc/postgresql/*/main/postgresql.conf`:

\`\`\`ini
shared_buffers = 256MB
effective_cache_size = 768MB
maintenance_work_mem = 128MB
work_mem = 16MB
\`\`\`

### Redis

Edit `/etc/redis/redis.conf`:

\`\`\`ini
maxmemory 512mb
maxmemory-policy allkeys-lru
\`\`\`

### Nginx

Adjust worker processes in `/etc/nginx/nginx.conf`:

\`\`\`nginx
worker_processes auto;
worker_connections 1024;
\`\`\`

## Support

For issues and questions:
- Review logs first
- Check this documentation
- Submit issues to the project repository

## License

This deployment guide is part of the ARCHITECT // VAULT project.
