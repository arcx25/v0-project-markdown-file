#!/bin/bash
# Install Monero daemon and wallet RPC

set -euo pipefail

echo "[+] Installing Monero..."

# Download Monero
MONERO_VERSION="v0.18.3.1"
MONERO_URL="https://downloads.getmonero.org/cli/monero-linux-x64-${MONERO_VERSION}.tar.bz2"

cd /tmp
wget -q "$MONERO_URL" -O monero.tar.bz2
tar -xjf monero.tar.bz2

# Install binaries
sudo mv monero-x86_64-linux-gnu-${MONERO_VERSION}/monerod /usr/local/bin/
sudo mv monero-x86_64-linux-gnu-${MONERO_VERSION}/monero-wallet-rpc /usr/local/bin/
sudo chmod +x /usr/local/bin/monerod /usr/local/bin/monero-wallet-rpc

# Clean up
rm -rf monero.tar.bz2 monero-x86_64-linux-gnu-${MONERO_VERSION}

echo "[+] Creating systemd service for monerod..."

cat > /tmp/monerod.service << 'EOF'
[Unit]
Description=Monero Daemon
After=network.target

[Service]
Type=simple
User=vault
Group=vault
WorkingDirectory=/var/lib/monero

ExecStart=/usr/local/bin/monerod \
    --data-dir=/var/lib/monero/blockchain \
    --log-file=/var/log/vault/monerod.log \
    --log-level=0 \
    --no-igd \
    --restricted-rpc \
    --rpc-bind-ip=127.0.0.1 \
    --rpc-bind-port=18081 \
    --confirm-external-bind

Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/monerod.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "[+] Creating systemd service for monero-wallet-rpc..."

cat > /tmp/monero-wallet-rpc.service << 'EOF'
[Unit]
Description=Monero Wallet RPC
After=network.target monerod.service
Requires=monerod.service

[Service]
Type=simple
User=vault
Group=vault
WorkingDirectory=/var/lib/monero/wallet

EnvironmentFile=/etc/vault/monero.env

ExecStart=/usr/local/bin/monero-wallet-rpc \
    --daemon-address=127.0.0.1:18081 \
    --rpc-bind-ip=127.0.0.1 \
    --rpc-bind-port=18083 \
    --wallet-dir=/var/lib/monero/wallet \
    --log-file=/var/log/vault/monero-wallet-rpc.log \
    --log-level=0 \
    --rpc-login=$MONERO_RPC_USER:$MONERO_RPC_PASSWORD \
    --disable-rpc-login=false \
    --confirm-external-bind

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/monero-wallet-rpc.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "[+] Monero installed successfully"
echo ""
echo "Configure /etc/vault/monero.env with:"
echo "  MONERO_RPC_USER=vault_rpc"
echo "  MONERO_RPC_PASSWORD=<secure-password>"
echo ""
echo "Then start services:"
echo "  sudo systemctl enable monerod monero-wallet-rpc"
echo "  sudo systemctl start monerod"
echo "  # Wait for sync, then:"
echo "  sudo systemctl start monero-wallet-rpc"
