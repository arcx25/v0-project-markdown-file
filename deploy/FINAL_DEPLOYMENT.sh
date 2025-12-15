#!/bin/bash

#########################################
# ARCHITECT // VAULT - Final Deployment
# Complete automated deployment to production
#########################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SERVER="${AVALANCHE_HOST:-91.98.16.255}"
USER="${AVALANCHE_USER:-root}"
APP_DIR="/opt/vault"
BACKUP_DIR="/var/backups/vault"

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ARCHITECT // VAULT                    ║${NC}"
echo -e "${GREEN}║  Final Production Deployment           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Validate prerequisites
echo -e "${YELLOW}[1/10] Validating prerequisites...${NC}"
if ! command -v ssh &> /dev/null; then
    echo -e "${RED}ERROR: ssh not found. Install openssh-client${NC}"
    exit 1
fi

if ! command -v rsync &> /dev/null; then
    echo -e "${RED}ERROR: rsync not found. Install rsync${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites validated${NC}"

# Test SSH connectivity
echo -e "${YELLOW}[2/10] Testing SSH connectivity...${NC}"
if ! ssh -o ConnectTimeout=10 "$USER@$SERVER" "echo 'SSH OK'" &> /dev/null; then
    echo -e "${RED}ERROR: Cannot connect to $SERVER${NC}"
    echo "Run: bash deploy/avalanche/setup_ssh.sh"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"

# Sync application code
echo -e "${YELLOW}[3/10] Syncing application code...${NC}"
rsync -avz --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv' \
    ./ "$USER@$SERVER:$APP_DIR/"
echo -e "${GREEN}✓ Code synced${NC}"

# Run server setup
echo -e "${YELLOW}[4/10] Running server setup...${NC}"
ssh "$USER@$SERVER" "cd $APP_DIR && bash deploy/scripts/setup_server.sh"
echo -e "${GREEN}✓ Server configured${NC}"

# Install Monero
echo -e "${YELLOW}[5/10] Installing Monero node...${NC}"
ssh "$USER@$SERVER" "cd $APP_DIR && bash deploy/scripts/install_monero.sh"
echo -e "${GREEN}✓ Monero installed${NC}"

# Configure environment
echo -e "${YELLOW}[6/10] Configuring environment...${NC}"
if [ -f ".env.production" ]; then
    scp .env.production "$USER@$SERVER:$APP_DIR/.env"
    echo -e "${GREEN}✓ Environment configured from .env.production${NC}"
else
    echo -e "${YELLOW}⚠ No .env.production found. Using server's existing .env${NC}"
fi

# Generate platform keys
echo -e "${YELLOW}[7/10] Generating platform keys...${NC}"
ssh "$USER@$SERVER" "cd $APP_DIR && python3 scripts/generate_platform_keys.py"
echo -e "${GREEN}✓ Platform keys generated${NC}"

# Initialize database
echo -e "${YELLOW}[8/10] Initializing database...${NC}"
ssh "$USER@$SERVER" "cd $APP_DIR && source venv/bin/activate && alembic upgrade head"
echo -e "${GREEN}✓ Database initialized${NC}"

# Create admin user
echo -e "${YELLOW}[9/10] Creating admin user...${NC}"
ssh "$USER@$SERVER" "cd $APP_DIR && source venv/bin/activate && python3 scripts/init_admin.py"
echo -e "${GREEN}✓ Admin user created${NC}"

# Install and start services
echo -e "${YELLOW}[10/10] Installing and starting services...${NC}"
ssh "$USER@$SERVER" "cd $APP_DIR && bash deploy/scripts/install_services.sh"
echo -e "${GREEN}✓ Services started${NC}"

# Final verification
echo ""
echo -e "${YELLOW}Running final verification...${NC}"
sleep 5

# Check service status
ssh "$USER@$SERVER" "systemctl status vault-web --no-pager" || true
ssh "$USER@$SERVER" "systemctl status vault-worker --no-pager" || true
ssh "$USER@$SERVER" "systemctl status vault-beat --no-pager" || true

# Get onion address
ONION_ADDRESS=$(ssh "$USER@$SERVER" "cat /var/lib/tor/vault/hostname 2>/dev/null || echo 'Not yet generated'")

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  DEPLOYMENT COMPLETE                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "Server: ${GREEN}$SERVER${NC}"
echo -e "Onion Address: ${GREEN}$ONION_ADDRESS${NC}"
echo -e "Health Check: ${GREEN}curl http://$SERVER:8000/health${NC}"
echo -e "API Docs: ${GREEN}http://$SERVER:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Save the onion address: $ONION_ADDRESS"
echo "2. Test health check: curl http://$SERVER:8000/health"
echo "3. Review logs: ssh $USER@$SERVER 'journalctl -u vault-web -f'"
echo "4. Access admin panel and verify functionality"
echo "5. Review PRODUCTION_CHECKLIST.md for final steps"
echo ""
echo -e "${GREEN}Deployment successful!${NC}"
