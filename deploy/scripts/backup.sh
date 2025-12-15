#!/bin/bash
# ARCHITECT // VAULT - Backup Script

set -euo pipefail

BACKUP_DIR="/var/lib/vault/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="vault_backup_${TIMESTAMP}"

mkdir -p $BACKUP_DIR

echo "[+] Starting backup: $BACKUP_NAME"

# Database backup
sudo -u postgres pg_dump vault | gzip > "${BACKUP_DIR}/${BACKUP_NAME}_db.sql.gz"
echo "[+] Database backed up"

# Keys backup
tar czf "${BACKUP_DIR}/${BACKUP_NAME}_keys.tar.gz" /var/lib/vault/gnupg/
echo "[+] Keys backed up"

# Config backup
tar czf "${BACKUP_DIR}/${BACKUP_NAME}_config.tar.gz" /etc/vault/
echo "[+] Config backed up"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "vault_backup_*" -mtime +7 -delete
echo "[+] Old backups cleaned"

echo "[+] Backup complete: $BACKUP_NAME"
