#!/bin/bash
# Install systemd service files

set -euo pipefail

echo "[+] Installing systemd service files..."

# Copy service files
sudo cp deploy/config/systemd/*.service /etc/systemd/system/

# Create run directory
sudo mkdir -p /var/run/vault
sudo chown vault:vault /var/run/vault

# Reload systemd
sudo systemctl daemon-reload

echo "[+] Service files installed"
echo ""
echo "Enable services with:"
echo "  sudo systemctl enable vault-web vault-worker vault-beat"
echo ""
echo "Start services with:"
echo "  sudo systemctl start vault-web vault-worker vault-beat"
