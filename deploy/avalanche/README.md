# ARCHITECT // VAULT - Avalanche Deployment

Deployment guide for Avalanche server at `91.98.16.255`

## Quick Start

### 1. Setup SSH Access
\`\`\`bash
bash deploy/avalanche/setup_ssh.sh
\`\`\`

This creates the SSH key and configures your SSH client.

### 2. Deploy Application
\`\`\`bash
bash deploy/avalanche/deploy_to_avalanche.sh
\`\`\`

This will:
- Package the application
- Upload to server
- Install all dependencies
- Configure PostgreSQL, Redis, Tor
- Setup systemd services
- Start the application

### 3. Post-Deployment

SSH into server:
\`\`\`bash
ssh avalanche
\`\`\`

Create admin user:
\`\`\`bash
cd /opt/architect-vault
source venv/bin/activate
python scripts/init_admin.py
\`\`\`

View logs:
\`\`\`bash
journalctl -u vault-web -f
journalctl -u vault-worker -f
\`\`\`

Check status:
\`\`\`bash
systemctl status vault-web
systemctl status vault-worker
systemctl status vault-beat
\`\`\`

## Quick Updates

For code updates without full redeployment:
\`\`\`bash
bash deploy/avalanche/quick_deploy.sh
\`\`\`

## Rollback

If something goes wrong:
\`\`\`bash
bash deploy/avalanche/rollback.sh
\`\`\`

## Server Information

- **IP**: 91.98.16.255
- **User**: root
- **App Directory**: /opt/architect-vault
- **Services**:
  - vault-web (FastAPI app)
  - vault-worker (Celery worker)
  - vault-beat (Celery beat scheduler)

## URLs

- **Direct**: http://localhost:8000
- **Via Nginx**: http://91.98.16.255
- **Tor Hidden Service**: Check `/var/lib/tor/architect_vault/hostname` on server

## Monitoring

\`\`\`bash
# All services
systemctl status vault-*

# Web logs
journalctl -u vault-web -f

# Worker logs
journalctl -u vault-worker -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Application logs
tail -f /opt/architect-vault/logs/app.log
\`\`\`

## Troubleshooting

### Service won't start
\`\`\`bash
journalctl -u vault-web -n 50
systemctl restart vault-web
\`\`\`

### Database issues
\`\`\`bash
sudo -u postgres psql
\l  # List databases
\c architect_vault  # Connect
\dt  # List tables
\`\`\`

### Python dependency issues
\`\`\`bash
cd /opt/architect-vault
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
\`\`\`

## Configuration

Edit environment variables:
\`\`\`bash
nano /opt/architect-vault/.env
systemctl restart vault-*
\`\`\`

## Security

- Firewall is configured via UFW
- Only ports 22 (SSH) and 80 (HTTP) are open
- Application runs as dedicated user
- Tor hidden service for anonymity
- All passwords are auto-generated on first deployment

## Backup

Manual backup:
\`\`\`bash
ssh avalanche "cd /opt/architect-vault && bash deploy/scripts/backup.sh"
\`\`\`

Backups are stored in `/opt/architect-vault/backups/`
