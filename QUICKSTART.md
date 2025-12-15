# ARCHITECT // VAULT - Quick Start Guide

This guide walks you through deploying ARCHITECT // VAULT from scratch in under 30 minutes.

## Prerequisites

- Fresh Debian 12 server (4GB RAM, 100GB SSD minimum)
- Root SSH access
- Local machine with SSH client

## Step 1: Initial Server Setup (10 minutes)

SSH to your server as root:

\`\`\`bash
ssh root@YOUR_SERVER_IP
\`\`\`

Download and run the setup script:

\`\`\`bash
cd /root
wget https://raw.githubusercontent.com/YOUR_REPO/main/deploy/scripts/setup_server.sh
chmod +x setup_server.sh
./setup_server.sh
\`\`\`

This will:
- Update system packages
- Install PostgreSQL, Redis, Tor, Nginx
- Configure firewall and fail2ban
- Create application user and directories
- Generate Tor hidden service

**Reboot the server when complete:**

\`\`\`bash
reboot
\`\`\`

## Step 2: Configure Local Deployment (5 minutes)

On your local machine, clone the repository:

\`\`\`bash
git clone https://github.com/YOUR_REPO/vault.git
cd vault
\`\`\`

Create deployment configuration:

\`\`\`bash
cp deploy/config/deploy.conf.template deploy/config/deploy.conf
\`\`\`

Edit `deploy/config/deploy.conf` with your server details:

\`\`\`bash
DEPLOY_HOST="YOUR_SERVER_IP"
DEPLOY_USER="vault"
SSH_KEY_PATH="$HOME/.ssh/id_rsa"
\`\`\`

The file includes commands to generate secure passwords automatically.

## Step 3: Generate Platform Keys (5 minutes)

SSH to the server as the vault user:

\`\`\`bash
ssh vault@YOUR_SERVER_IP
cd /opt/vault
\`\`\`

Clone the repository:

\`\`\`bash
git clone https://github.com/YOUR_REPO/vault.git .
\`\`\`

Create Python virtual environment:

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install gnupg
\`\`\`

Generate platform PGP keys:

\`\`\`bash
python3 scripts/generate_platform_keys.py
\`\`\`

**Important:** Save the passphrase and fingerprint shown!

Update `/etc/vault/environment`:

\`\`\`bash
sudo nano /etc/vault/environment
\`\`\`

Add the PGP fingerprint and passphrase from the output.

## Step 4: Deploy Application (5 minutes)

From your local machine:

\`\`\`bash
cd vault
chmod +x deploy/scripts/*.sh
./deploy/scripts/deploy.sh
\`\`\`

This will:
- Upload application code
- Install Python dependencies
- Run database migrations
- Configure environment
- Start all services

## Step 5: Get Your Onion Address (1 minute)

On the server:

\`\`\`bash
cat /var/lib/tor/vault/hostname
\`\`\`

Copy this `.onion` address.

## Step 6: Create Admin Account (3 minutes)

Generate a PGP keypair for your admin account (on your local machine):

\`\`\`bash
gpg --full-generate-key
# Select: (9) ECC (sign and encrypt)
# Select: (1) Curve 25519
# Name: Admin
# Email: admin@vault.local
\`\`\`

Export your public key:

\`\`\`bash
gpg --armor --export admin@vault.local > admin_public.asc
\`\`\`

On the server, create admin user:

\`\`\`bash
ssh vault@YOUR_SERVER_IP
cd /opt/vault
source venv/bin/activate

# Set environment
export INITIAL_ADMIN_USERNAME="admin"
export INITIAL_ADMIN_PGP_KEY="$(cat ~/admin_public.asc)"

# Create admin
python scripts/init_admin.py
\`\`\`

## Step 7: Access Platform (1 minute)

1. Open **Tor Browser**
2. Navigate to: `http://YOUR_ONION_ADDRESS.onion`
3. Click "Login"
4. Import your admin private key when prompted
5. Complete PGP challenge authentication

## Done!

Your ARCHITECT // VAULT instance is now running!

## Next Steps

### Optional: Install Monero Support

\`\`\`bash
ssh vault@YOUR_SERVER_IP
cd /opt/vault
sudo ./deploy/scripts/install_monero.sh
\`\`\`

### Setup Automated Backups

Add to crontab:

\`\`\`bash
sudo crontab -e
\`\`\`

Add:

\`\`\`
0 2 * * * /opt/vault/deploy/scripts/backup.sh
\`\`\`

### Monitor Health

\`\`\`bash
/opt/vault/deploy/scripts/health_check.sh
\`\`\`

### View Logs

\`\`\`bash
sudo journalctl -u vault-web -f
\`\`\`

## Troubleshooting

### Services won't start

Check logs:
\`\`\`bash
sudo journalctl -u vault-web --no-pager | tail -50
\`\`\`

### Can't access onion address

Verify Tor is running:
\`\`\`bash
sudo systemctl status tor
cat /var/lib/tor/vault/hostname
\`\`\`

### Database errors

Check PostgreSQL:
\`\`\`bash
sudo systemctl status postgresql
sudo -u postgres psql vault
\`\`\`

## Security Checklist

- [ ] Changed default SSH port
- [ ] Disabled password authentication (keys only)
- [ ] Configured firewall (UFW)
- [ ] Enabled automatic security updates
- [ ] Generated strong database passwords
- [ ] Backed up PGP keys securely
- [ ] Set up automated backups
- [ ] Reviewed fail2ban configuration

## Support

For issues, check:
- `DEPLOYMENT.md` for detailed deployment guide
- Application logs: `/var/log/vault/app.log`
- System logs: `sudo journalctl -xe`

Your platform is now operational and accessible via Tor!
