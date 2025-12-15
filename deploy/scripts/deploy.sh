#!/bin/bash
# ARCHITECT // VAULT - Deployment Script

set -euo pipefail

echo "ARCHITECT // VAULT - Deployment"
echo "================================"
echo ""

# Load config
source deploy/config/deploy.conf

echo "[+] Deploying to $DEPLOY_HOST"
echo "[+] Application directory: $APP_DIR"
echo ""

# Upload code
echo "[+] Uploading application code..."
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    -e "ssh -p $DEPLOY_PORT -i $SSH_KEY_PATH" \
    . ${DEPLOY_USER}@${DEPLOY_HOST}:${APP_DIR}/

# Install dependencies
echo "[+] Installing dependencies..."
ssh -p $DEPLOY_PORT -i $SSH_KEY_PATH ${DEPLOY_USER}@${DEPLOY_HOST} << 'ENDSSH'
cd /opt/vault
source venv/bin/activate
pip install -r requirements.txt
ENDSSH

# Run migrations
echo "[+] Running database migrations..."
ssh -p $DEPLOY_PORT -i $SSH_KEY_PATH ${DEPLOY_USER}@${DEPLOY_HOST} << 'ENDSSH'
cd /opt/vault
source venv/bin/activate
alembic upgrade head
ENDSSH

# Restart services
echo "[+] Restarting services..."
ssh -p $DEPLOY_PORT -i $SSH_KEY_PATH ${DEPLOY_USER}@${DEPLOY_HOST} << 'ENDSSH'
sudo systemctl restart vault-web
sudo systemctl restart vault-worker
sudo systemctl restart vault-beat
ENDSSH

echo ""
echo "[+] Deployment complete!"
echo "[+] Check service status: systemctl status vault-web"
