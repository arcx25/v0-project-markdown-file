#!/bin/bash
# ARCHITECT // VAULT - Rollback Script

set -euo pipefail

BACKUP_DIR="/var/lib/vault/backups"

echo "ARCHITECT // VAULT - Rollback"
echo "=============================="
echo ""

# List available backups
echo "Available backups:"
ls -lth $BACKUP_DIR/*.tar.gz | head -10
echo ""

read -p "Enter backup timestamp (YYYYMMDD_HHMMSS): " TIMESTAMP
BACKUP_NAME="vault_backup_${TIMESTAMP}"

if [ ! -f "${BACKUP_DIR}/${BACKUP_NAME}_app.tar.gz" ]; then
    echo "[!] Backup not found: ${BACKUP_NAME}_app.tar.gz"
    exit 1
fi

read -p "This will restore from backup. Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

echo "[+] Stopping services..."
sudo systemctl stop vault-web vault-worker vault-beat

echo "[+] Restoring application..."
cd /opt/vault
sudo -u vault tar -xzf "${BACKUP_DIR}/${BACKUP_NAME}_app.tar.gz"

echo "[+] Restoring database..."
if [ -f "${BACKUP_DIR}/${BACKUP_NAME}_db.sql.gz" ]; then
    gunzip -c "${BACKUP_DIR}/${BACKUP_NAME}_db.sql.gz" | sudo -u postgres psql vault
else
    echo "[!] No database backup found, skipping"
fi

echo "[+] Starting services..."
sudo systemctl start vault-web vault-worker vault-beat

echo "[+] Rollback complete!"
