# Quick Deployment Guide

## Run in IDE

Execute the setup script directly in your IDE:

\`\`\`bash
python3 scripts/setup_deployment.py
\`\`\`

This will:
1. ✅ Generate SSH keys
2. ✅ Show you what to copy to your server
3. ✅ Guide you through GitHub secrets setup
4. ✅ Configure the deployment pipeline

## Quick Deploy (After Setup)

Deploy immediately without waiting for Git push:

\`\`\`bash
python3 scripts/deploy_now.py
\`\`\`

## Environment Variables

Set these before running (optional):

\`\`\`bash
export SERVER_USER=avalanche
export SERVER_HOST=91.98.16.255
export SERVER_PORT=22
export SSH_PRIVATE_KEY_PATH=~/.ssh/vault_deploy_key
\`\`\`

## Manual Steps

If the scripts don't work in your IDE, follow these manual steps:

### 1. Generate SSH Key (on your local machine)
\`\`\`bash
ssh-keygen -t ed25519 -f ~/.ssh/vault_deploy_key -N ""
\`\`\`

### 2. Copy Key to Server
\`\`\`bash
ssh-copy-id -i ~/.ssh/vault_deploy_key.pub avalanche@91.98.16.255
\`\`\`

### 3. Add GitHub Secrets

Go to: Your Repo → Settings → Secrets → Actions → New secret

Add these:
- `SSH_PRIVATE_KEY`: Contents of `~/.ssh/vault_deploy_key`
- `SERVER_HOST`: `91.98.16.255`
- `SERVER_USER`: `avalanche`
- `SERVER_PORT`: `22`

### 4. Push to Deploy

\`\`\`bash
git add .
git commit -m "Deploy ARCHITECT // VAULT"
git push origin main
\`\`\`

Watch deployment: GitHub → Actions tab

## Troubleshooting

**Script can't find ssh-keygen:**
- Install OpenSSH: `sudo apt install openssh-client` (Linux)
- macOS: Already installed
- Windows: Install Git Bash or WSL

**Permission denied:**
\`\`\`bash
chmod +x scripts/*.py
\`\`\`

**Can't connect to server:**
- Verify server is running: `ping 91.98.16.255`
- Check SSH port: `nc -zv 91.98.16.255 22`
- Verify credentials with Avalanche support
