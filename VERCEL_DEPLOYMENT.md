# Vercel CI/CD Deployment Guide

This setup uses Vercel + GitHub Actions to automatically deploy your Python backend to the Avalanche server.

## Setup Steps

### 1. Push to GitHub

\`\`\`bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/architect-vault.git
git push -u origin main
\`\`\`

### 2. Configure GitHub Secrets

Go to: `https://github.com/YOUR_USERNAME/architect-vault/settings/secrets/actions`

Add these secrets:

- **AVALANCHE_SERVER**: `91.98.16.255`
- **AVALANCHE_USER**: `avalanche`
- **AVALANCHE_SSH_KEY**: Your private SSH key (paste the entire key)

\`\`\`bash
# Generate SSH key if you don't have one:
ssh-keygen -t ed25519 -C "deploy@architect-vault"

# Copy private key:
cat ~/.ssh/id_ed25519
# Paste this into AVALANCHE_SSH_KEY secret

# Copy public key to server:
ssh-copy-id avalanche@91.98.16.255
\`\`\`

### 3. Connect to Vercel

1. Go to https://vercel.com
2. Import your GitHub repository
3. Set Framework Preset: **Other**
4. Build Command: `cd frontend && npm install && npm run build`
5. Output Directory: `frontend/dist`
6. Deploy!

### 4. Automatic Deployments

Now every time you push to `main`:

1. **Vercel** builds the frontend dashboard
2. **GitHub Actions** SSH into your Avalanche server
3. **Backend** gets pulled, updated, and restarted automatically

## Manual Deployment

Trigger manually from GitHub:

\`\`\`
Actions → Deploy to Avalanche Server → Run workflow
\`\`\`

## How It Works

\`\`\`
┌─────────┐      ┌─────────┐      ┌──────────────┐      ┌─────────────┐
│   You   │─────▶│ GitHub  │─────▶│ GitHub       │─────▶│  Avalanche  │
│  Push   │      │  Repo   │      │  Actions     │ SSH  │   Server    │
└─────────┘      └─────────┘      └──────────────┘      └─────────────┘
                      │                                          │
                      │                                          │
                      ▼                                          │
                 ┌─────────┐                                     │
                 │ Vercel  │                                     │
                 │Frontend │◀────────────────────────────────────┘
                 └─────────┘       (API calls via proxy)
\`\`\`

## Monitoring

- **Frontend Dashboard**: https://YOUR_PROJECT.vercel.app
- **GitHub Actions**: https://github.com/YOUR_REPO/actions
- **Backend API**: http://91.98.16.255:8000/docs
- **Server SSH**: `ssh avalanche@91.98.16.255`

## Rollback

If deployment fails:

\`\`\`bash
ssh avalanche@91.98.16.255
cd /opt/architect-vault
ls -la | grep backup  # Find backup
sudo cp -r /opt/architect-vault.backup.YYYYMMDD-HHMMSS/* /opt/architect-vault/
sudo systemctl restart vault-web vault-worker vault-beat
