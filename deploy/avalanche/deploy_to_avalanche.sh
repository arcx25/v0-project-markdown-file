#!/bin/bash
set -e

# ARCHITECT // VAULT - Avalanche Deployment Script
# This script automates deployment to the Avalanche server

echo "======================================"
echo "ARCHITECT // VAULT - Avalanche Deploy"
echo "======================================"

# Configuration
SERVER_IP="91.98.16.255"
SERVER_USER="root"
SSH_KEY="~/avalanche_key"
REMOTE_DIR="/opt/architect-vault"
APP_NAME="architect-vault"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    log_error "SSH key not found at $SSH_KEY"
    echo "Creating SSH key..."
    
    cat > "$SSH_KEY" << 'EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACA2RgFm8IbN8PEne/JMVICr1UmUrFe0+0shOPn8xSCfOwAAAKA3rBdJN6wX
SQAAAAtzc2gtZWQyNTUxOQAAACA2RgFm8IbN8PEne/JMVICr1UmUrFe0+0shOPn8xSCfOw
AAAEA/1Kd8+UqEzK6/Rym4mbPPLkhEH+/AeFHguzMOzveBszZGAWbwhs3w8Sd78kxUgKvV
SZSsV7T7SyE4+fzFIJ87AAAAHGFnZW50MkBhcmNoaXRlY3QtbWFya2V0cGxhY2UB
-----END OPENSSH PRIVATE KEY-----
EOF
    
    chmod 600 "$SSH_KEY"
    log_success "SSH key created and permissions set"
fi

# Test connection
log_info "Testing connection to server..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo 'Connection successful'" &>/dev/null; then
    log_error "Cannot connect to server. Please check network and credentials."
    exit 1
fi
log_success "Connection successful"

# Create deployment package
log_info "Creating deployment package..."
cd "$(dirname "$0")/../.."
tar --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.env' \
    --exclude='node_modules' \
    --exclude='.next' \
    -czf /tmp/architect-vault-deploy.tar.gz .
log_success "Deployment package created"

# Upload to server
log_info "Uploading application to server..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no /tmp/architect-vault-deploy.tar.gz "$SERVER_USER@$SERVER_IP:/tmp/"
log_success "Upload complete"

# Deploy on server
log_info "Deploying application on server..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" bash <<'REMOTE_SCRIPT'
set -e

echo "[Remote] Starting deployment..."

# Install system dependencies
echo "[Remote] Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib \
    redis-server tor nginx git curl gnupg2 build-essential libpq-dev

# Create application directory
echo "[Remote] Setting up application directory..."
mkdir -p /opt/architect-vault
cd /opt/architect-vault

# Extract application
echo "[Remote] Extracting application..."
tar -xzf /tmp/architect-vault-deploy.tar.gz -C /opt/architect-vault
rm /tmp/architect-vault-deploy.tar.gz

# Create Python virtual environment
echo "[Remote] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "[Remote] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "[Remote] Creating .env configuration..."
    cp .env.example .env
    
    # Generate secrets
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
    
    # Update .env
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DB_PASSWORD/" .env
    sed -i "s/DATABASE_URL=.*/DATABASE_URL=postgresql:\/\/architect:$DB_PASSWORD@localhost\/architect_vault/" .env
fi

# Setup PostgreSQL
echo "[Remote] Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE USER architect WITH PASSWORD 'changeme';" || true
sudo -u postgres psql -c "CREATE DATABASE architect_vault OWNER architect;" || true
sudo -u postgres psql -c "ALTER USER architect WITH SUPERUSER;" || true

# Run migrations
echo "[Remote] Running database migrations..."
source venv/bin/activate
alembic upgrade head

# Setup Tor hidden service
echo "[Remote] Configuring Tor hidden service..."
cat > /etc/tor/torrc << 'TORRC'
HiddenServiceDir /var/lib/tor/architect_vault/
HiddenServicePort 80 127.0.0.1:8000
TORRC

systemctl restart tor
sleep 5

# Get onion address
if [ -f /var/lib/tor/architect_vault/hostname ]; then
    ONION_ADDRESS=$(cat /var/lib/tor/architect_vault/hostname)
    echo "[Remote] Tor Hidden Service: $ONION_ADDRESS"
    echo "$ONION_ADDRESS" > /opt/architect-vault/onion_address.txt
fi

# Install systemd services
echo "[Remote] Installing systemd services..."
cp deploy/config/systemd/*.service /etc/systemd/system/
systemctl daemon-reload

# Start services
echo "[Remote] Starting services..."
systemctl enable vault-web vault-worker vault-beat
systemctl restart vault-web vault-worker vault-beat

# Setup Nginx
echo "[Remote] Configuring Nginx..."
cp deploy/config/nginx/vault.conf /etc/nginx/sites-available/architect-vault
ln -sf /etc/nginx/sites-available/architect-vault /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "[Remote] Deployment complete!"
echo "[Remote] Application is running at http://localhost:8000"
echo "[Remote] Check status: systemctl status vault-web"

REMOTE_SCRIPT

log_success "Deployment complete!"

# Get server status
log_info "Fetching deployment information..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" bash <<'STATUS'
echo ""
echo "======================================"
echo "Deployment Status"
echo "======================================"
echo ""
echo "Services:"
systemctl status vault-web --no-pager -l | head -n 3
echo ""
echo "Tor Hidden Service:"
if [ -f /var/lib/tor/architect_vault/hostname ]; then
    cat /var/lib/tor/architect_vault/hostname
else
    echo "Tor hidden service not ready yet. Check back in 60 seconds."
fi
echo ""
echo "Local URLs:"
echo "  - http://localhost:8000 (Direct)"
echo "  - http://127.0.0.1 (Via Nginx)"
echo ""
echo "Logs:"
echo "  - journalctl -u vault-web -f"
echo "  - journalctl -u vault-worker -f"
echo ""
STATUS

log_success "All done! Your ARCHITECT // VAULT is deployed."
echo ""
echo "Next steps:"
echo "1. SSH into server: ssh -i ~/avalanche_key root@91.98.16.255"
echo "2. Create admin user: cd /opt/architect-vault && source venv/bin/activate && python scripts/init_admin.py"
echo "3. Configure environment: nano /opt/architect-vault/.env"
echo "4. View logs: journalctl -u vault-web -f"
