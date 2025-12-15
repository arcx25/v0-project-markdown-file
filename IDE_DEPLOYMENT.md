# IDE Deployment Guide

Deploy ARCHITECT // VAULT directly from your IDE without system dependencies.

## Prerequisites

\`\`\`bash
pip install cryptography paramiko
\`\`\`

## Quick Start

### 1. Setup (One-Time)

\`\`\`bash
python3 scripts/setup_deployment.py
\`\`\`

This will:
- Generate SSH keys using pure Python
- Show you the public key to add to your server
- Display GitHub secrets to configure

### 2. Deploy

**Option A: Manual Deployment (from IDE)**
\`\`\`bash
python3 scripts/deploy_manual.py
\`\`\`

**Option B: Automatic Deployment (GitHub Actions)**
\`\`\`bash
git push origin main
\`\`\`

## Detailed Steps

### Add SSH Key to Server

SSH to your Avalanche server:
\`\`\`bash
ssh avalanche@91.98.16.255
\`\`\`

Add the public key shown by setup script:
\`\`\`bash
mkdir -p ~/.ssh
echo 'YOUR_PUBLIC_KEY_HERE' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
\`\`\`

### Configure GitHub Secrets

Go to your repository: Settings → Secrets → Actions

Add these secrets:
- `SSH_PRIVATE_KEY`: Private key from setup script
- `SERVER_HOST`: `91.98.16.255`
- `SERVER_USER`: `avalanche`
- `SERVER_PORT`: `22`

### Deploy

Run from your IDE:
\`\`\`bash
python3 scripts/deploy_manual.py
\`\`\`

Or push to trigger GitHub Actions:
\`\`\`bash
git add .
git commit -m "Deploy"
git push origin main
\`\`\`

## Troubleshooting

**SSH Connection Failed**
- Verify server is accessible: `ping 91.98.16.255`
- Check SSH key permissions: `ls -la ~/.ssh/vault_deploy_key`
- Ensure public key is on server: `ssh avalanche@91.98.16.255 cat ~/.ssh/authorized_keys`

**Paramiko Not Found**
\`\`\`bash
pip install paramiko
\`\`\`

**Cryptography Not Found**
\`\`\`bash
pip install cryptography
\`\`\`

## What Gets Deployed

The deployment includes:
- All Python application code (`app/`)
- Configuration files
- Database migrations (`alembic/`)
- Deployment scripts (`deploy/`)
- Requirements file

Excluded:
- `.git/` directory
- `__pycache__/` and `*.pyc`
- Virtual environments
- Node modules
- Local `.env` files

## Post-Deployment

Check deployment status:
\`\`\`bash
ssh avalanche@91.98.16.255 'sudo systemctl status vault-web'
\`\`\`

View logs:
\`\`\`bash
ssh avalanche@91.98.16.255 'sudo journalctl -u vault-web -f'
\`\`\`

Get Tor onion address:
\`\`\`bash
ssh avalanche@91.98.16.255 'sudo cat /var/lib/tor/vault/hostname'
