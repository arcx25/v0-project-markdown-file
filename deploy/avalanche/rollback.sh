#!/bin/bash
# Rollback to previous deployment

set -e

SERVER="root@91.98.16.255"
KEY="~/avalanche_key"

echo "Rolling back deployment on Avalanche..."

ssh -i $KEY $SERVER << 'EOF'
cd /opt/architect-vault
if [ -d "backup_previous" ]; then
    echo "Restoring from backup..."
    rm -rf current/*
    cp -r backup_previous/* current/
    cd current
    source venv/bin/activate
    systemctl restart vault-web vault-worker vault-beat
    echo "Rollback complete!"
else
    echo "No backup found!"
    exit 1
fi
EOF
