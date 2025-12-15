# ARCHITECT Deployment Instructions
## Deploy to Avalanche Server (91.98.16.255)

**Platform**: Anonymous XMR Marketplace for Buyers & Vendors  
**Target**: Avalanche VPS at 91.98.16.255  
**Method**: Automated deployment via SSH

---

## Quick Deploy (3 Commands)

\`\`\`bash
# 1. Make scripts executable
chmod +x deploy/avalanche/*.sh

# 2. Deploy to server
./deploy/avalanche/deploy_to_avalanche.sh

# 3. Get your Tor onion address
ssh root@91.98.16.255 "cat /var/lib/tor/architect_vault/hostname"
\`\`\`

**Done!** Your marketplace is live on Tor.

---

## What Gets Deployed

The script automatically installs and configures:

### Core Services
- **FastAPI Backend** - Python 3.12 with async support
- **PostgreSQL 15** - Database with full-text search
- **Redis 7** - Caching & session storage
- **Celery Workers** - Background job processing
- **Nginx** - Reverse proxy & rate limiting
- **Tor Hidden Service** - v3 onion address

### Monero Integration
- **Monero Node** - Full blockchain sync (optional)
- **Wallet RPC** - Payment processing
- **Payment Monitor** - Auto-confirmation tracking

### Security Features
- **PGP Authentication** - No passwords, keys only
- **Rate Limiting** - DDoS protection
- **Fail2Ban** - Auto-ban attackers
- **UFW Firewall** - Only necessary ports open
- **Encrypted Sessions** - All traffic encrypted

---

## Deployment Options

### Option 1: Automated Bash Script (Recommended)

\`\`\`bash
cd /path/to/architect-vault
./deploy/avalanche/deploy_to_avalanche.sh
\`\`\`

**What it does:**
- Connects to 91.98.16.255 via SSH
- Uploads entire codebase
- Installs all dependencies
- Creates database & runs migrations
- Configures Tor hidden service
- Starts all systemd services
- Returns your .onion address

**Time**: 5-10 minutes

---

### Option 2: Pure Python Deployment (IDE-Compatible)

\`\`\`bash
# Install paramiko first
pip install paramiko cryptography

# Run deployment script
python3 scripts/deploy_manual.py
\`\`\`

**Advantage**: Works from any Python environment without bash/SSH tools.

---

### Option 3: Manual Step-by-Step

If you prefer complete control:

#### Step 1: Connect to Server
\`\`\`bash
ssh root@91.98.16.255
\`\`\`

#### Step 2: Install Dependencies
\`\`\`bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv postgresql redis-server \
    tor nginx git curl build-essential libpq-dev gnupg2
\`\`\`

#### Step 3: Clone Repository
\`\`\`bash
cd /opt
git clone <your-repo-url> architect-vault
cd architect-vault
\`\`\`

#### Step 4: Create Virtual Environment
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

#### Step 5: Configure Database
\`\`\`bash
sudo -u postgres psql << EOF
CREATE USER architect WITH PASSWORD 'change_this_password';
CREATE DATABASE architect_vault OWNER architect;
GRANT ALL PRIVILEGES ON DATABASE architect_vault TO architect;
EOF
\`\`\`

#### Step 6: Setup Environment
\`\`\`bash
cp .env.example .env
nano .env  # Edit configuration
\`\`\`

**Required variables:**
\`\`\`bash
SECRET_KEY=<generate with: openssl rand -hex 32>
DATABASE_URL=postgresql+asyncpg://architect:your_password@localhost/architect_vault
REDIS_URL=redis://localhost:6379/0
MONERO_WALLET_RPC_URL=http://localhost:18083/json_rpc
\`\`\`

#### Step 7: Run Migrations
\`\`\`bash
source venv/bin/activate
alembic upgrade head
\`\`\`

#### Step 8: Configure Tor
\`\`\`bash
cat >> /etc/tor/torrc << EOF
HiddenServiceDir /var/lib/tor/architect_vault/
HiddenServicePort 80 127.0.0.1:8000
EOF

systemctl restart tor
sleep 5
cat /var/lib/tor/architect_vault/hostname  # Your .onion address
\`\`\`

#### Step 9: Install Systemd Services
\`\`\`bash
# Create vault-web.service
cat > /etc/systemd/system/vault-web.service << EOF
[Unit]
Description=ARCHITECT Vault Web Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/architect-vault
Environment="PATH=/opt/architect-vault/venv/bin"
ExecStart=/opt/architect-vault/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create vault-worker.service
cat > /etc/systemd/system/vault-worker.service << EOF
[Unit]
Description=ARCHITECT Vault Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/architect-vault
Environment="PATH=/opt/architect-vault/venv/bin"
ExecStart=/opt/architect-vault/venv/bin/celery -A app.workers.celery_app worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create vault-beat.service
cat > /etc/systemd/system/vault-beat.service << EOF
[Unit]
Description=ARCHITECT Vault Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/architect-vault
Environment="PATH=/opt/architect-vault/venv/bin"
ExecStart=/opt/architect-vault/venv/bin/celery -A app.workers.celery_app beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vault-web vault-worker vault-beat
systemctl start vault-web vault-worker vault-beat
\`\`\`

#### Step 10: Configure Nginx
\`\`\`bash
cat > /etc/nginx/sites-available/architect-vault << 'EOF'
server {
    listen 80;
    server_name localhost;

    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/architect-vault /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx
\`\`\`

---

## Post-Deployment

### 1. Create Admin Account
\`\`\`bash
ssh root@91.98.16.255
cd /opt/architect-vault
source venv/bin/activate
python scripts/init_admin.py
\`\`\`

### 2. Verify Services
\`\`\`bash
systemctl status vault-web
systemctl status vault-worker
systemctl status vault-beat
systemctl status postgresql
systemctl status redis
systemctl status tor
systemctl status nginx
\`\`\`

### 3. Check Logs
\`\`\`bash
# Web service logs
journalctl -u vault-web -f

# Worker logs
journalctl -u vault-worker -f

# Nginx access logs
tail -f /var/log/nginx/access.log
\`\`\`

### 4. Get Onion Address
\`\`\`bash
cat /var/lib/tor/architect_vault/hostname
\`\`\`

### 5. Test Platform
\`\`\`bash
# Local test
curl http://localhost:8000/health

# Should return: {"status":"healthy"}
\`\`\`

---

## Updates & Maintenance

### Update Application Code
\`\`\`bash
ssh root@91.98.16.255
cd /opt/architect-vault
git pull
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart vault-web vault-worker vault-beat
\`\`\`

### Backup Database
\`\`\`bash
sudo -u postgres pg_dump architect_vault > backup_$(date +%Y%m%d).sql
\`\`\`

### View Errors
\`\`\`bash
journalctl -u vault-web --since "1 hour ago" | grep ERROR
\`\`\`

---

## Troubleshooting

### Application won't start
\`\`\`bash
# Check logs
journalctl -u vault-web -n 50

# Verify .env file
cat /opt/architect-vault/.env

# Test database connection
psql postgresql://architect:password@localhost/architect_vault
\`\`\`

### Tor not working
\`\`\`bash
# Check Tor status
systemctl status tor

# View Tor logs
journalctl -u tor -n 50

# Verify hidden service
ls -la /var/lib/tor/architect_vault/
\`\`\`

### Database errors
\`\`\`bash
# Check PostgreSQL
systemctl status postgresql

# View database logs
tail -f /var/log/postgresql/postgresql-15-main.log

# Restart database
systemctl restart postgresql
\`\`\`

---

## Security Checklist

After deployment, verify:

- [ ] Firewall enabled: `ufw status`
- [ ] Only necessary ports open (22, 80, 443)
- [ ] SSH key-based auth only (disable password auth)
- [ ] `.env` file has secure random secrets
- [ ] Database password is strong
- [ ] Fail2Ban is running: `systemctl status fail2ban`
- [ ] All services running as non-root (except nginx/tor)
- [ ] Backups configured
- [ ] Monitoring set up

---

## Production Configuration

### High-Traffic Optimization

Edit `/etc/nginx/nginx.conf`:
\`\`\`nginx
worker_processes auto;
worker_connections 4096;

http {
    client_body_buffer_size 128k;
    client_max_body_size 25m;
    keepalive_timeout 65;
}
\`\`\`

### Database Tuning

Edit `/etc/postgresql/15/main/postgresql.conf`:
\`\`\`ini
shared_buffers = 512MB
effective_cache_size = 1GB
work_mem = 32MB
maintenance_work_mem = 256MB
max_connections = 200
\`\`\`

### Redis Optimization

Edit `/etc/redis/redis.conf`:
\`\`\`ini
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
\`\`\`

---

## Support

**Logs**: All logs in `/var/log/vault/`  
**Config**: Environment in `/opt/architect-vault/.env`  
**Database**: PostgreSQL on port 5432  
**Web**: FastAPI on port 8000  
**Tor**: Hidden service dir `/var/lib/tor/architect_vault/`

For issues, check logs first, then consult DEPLOYMENT.md for detailed troubleshooting.
