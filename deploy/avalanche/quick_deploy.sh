#!/bin/bash
# Quick deployment script - minimal steps

set -e

SERVER="root@91.98.16.255"
KEY="~/avalanche_key"

echo "Quick deploying to Avalanche..."

# Create archive
tar czf /tmp/vault.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    .

# Upload
scp -i $KEY /tmp/vault.tar.gz $SERVER:/tmp/

# Deploy
ssh -i $KEY $SERVER << 'EOF'
cd /opt/architect-vault
tar xzf /tmp/vault.tar.gz
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
systemctl restart vault-web vault-worker vault-beat
echo "Deployment complete!"
systemctl status vault-web --no-pager | head -n 3
EOF

echo "Done! Services restarted."
