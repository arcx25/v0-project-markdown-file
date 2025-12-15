#!/bin/bash
# =============================================================================
# ARCHITECT // VAULT - Initial Server Setup
# =============================================================================
#
# This script prepares a fresh Debian 12 server for deployment.
# Run this ONCE on a new server.
#
# Usage: ./setup_server.sh
#
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${PURPLE}═══════════════════════════════════════════════════════════${NC}"; echo -e "${PURPLE}  $1${NC}"; echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}\n"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root"
   exit 1
fi

# =============================================================================
# CONFIGURATION
# =============================================================================

APP_USER="vault"
APP_DIR="/opt/vault"
DATA_DIR="/var/lib/vault"
LOG_DIR="/var/log/vault"
MONERO_DIR="/var/lib/monero"

# =============================================================================
# SYSTEM UPDATE
# =============================================================================

log_section "Updating System"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get dist-upgrade -y

log_success "System updated"

# =============================================================================
# INSTALL DEPENDENCIES
# =============================================================================

log_section "Installing Dependencies"

DEBIAN_FRONTEND=noninteractive apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    software-properties-common \
    build-essential \
    git \
    vim \
    htop \
    tmux \
    ufw \
    fail2ban \
    unattended-upgrades \
    apt-listchanges \
    logrotate \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    certbot \
    tor \
    deb.torproject.org-keyring

log_success "Dependencies installed"

# =============================================================================
# CREATE APPLICATION USER
# =============================================================================

log_section "Creating Application User"

if id "$APP_USER" &>/dev/null; then
    log_warning "User $APP_USER already exists"
else
    useradd -m -s /bin/bash -d /home/$APP_USER $APP_USER
    log_success "User $APP_USER created"
fi

# =============================================================================
# CREATE DIRECTORIES
# =============================================================================

log_section "Creating Directories"

mkdir -p $APP_DIR
mkdir -p $DATA_DIR/{gnupg,uploads,backups}
mkdir -p $LOG_DIR
mkdir -p $MONERO_DIR/{blockchain,wallet}
mkdir -p /etc/vault

# Set permissions
chown -R $APP_USER:$APP_USER $APP_DIR
chown -R $APP_USER:$APP_USER $DATA_DIR
chown -R $APP_USER:$APP_USER $LOG_DIR
chmod 700 $DATA_DIR/gnupg

log_success "Directories created"

# =============================================================================
# CONFIGURE FIREWALL
# =============================================================================

log_section "Configuring Firewall"

ufw default deny incoming
ufw default allow outgoing

# SSH (change port if needed)
ufw allow 22/tcp comment 'SSH'

# HTTP/HTTPS (for Let's Encrypt and clearnet access)
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Monero P2P (optional, for full node)
ufw allow 18080/tcp comment 'Monero P2P'

# Enable firewall
ufw --force enable

log_success "Firewall configured"

# =============================================================================
# CONFIGURE FAIL2BAN
# =============================================================================

log_section "Configuring Fail2Ban"

cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 5
EOF

systemctl enable fail2ban
systemctl restart fail2ban

log_success "Fail2Ban configured"

# =============================================================================
# CONFIGURE AUTOMATIC UPDATES
# =============================================================================

log_section "Configuring Automatic Updates"

cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

log_success "Automatic updates configured"

# =============================================================================
# CONFIGURE POSTGRESQL
# =============================================================================

log_section "Configuring PostgreSQL"

systemctl enable postgresql
systemctl start postgresql

sudo -u postgres psql << 'EOF'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'vault') THEN
        CREATE ROLE vault WITH LOGIN PASSWORD 'PLACEHOLDER_CHANGE_ME';
    END IF;
END
$$;

SELECT 'CREATE DATABASE vault OWNER vault'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vault')\gexec

\c vault
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOF

systemctl restart postgresql

log_success "PostgreSQL configured"

# =============================================================================
# CONFIGURE REDIS
# =============================================================================

log_section "Configuring Redis"

systemctl enable redis-server
systemctl restart redis-server

log_success "Redis configured"

# =============================================================================
# CONFIGURE TOR
# =============================================================================

log_section "Configuring Tor"

cat > /etc/tor/torrc << 'EOF'
Log notice file /var/log/tor/notices.log
HiddenServiceDir /var/lib/tor/vault/
HiddenServicePort 80 127.0.0.1:8000
HiddenServiceVersion 3
SafeLogging 1
EOF

mkdir -p /var/lib/tor/vault
chown -R debian-tor:debian-tor /var/lib/tor/vault
chmod 700 /var/lib/tor/vault

systemctl enable tor
systemctl restart tor

sleep 5

if [ -f /var/lib/tor/vault/hostname ]; then
    ONION_ADDRESS=$(cat /var/lib/tor/vault/hostname)
    log_success "Tor hidden service created: $ONION_ADDRESS"
fi

# =============================================================================
# CONFIGURE NGINX
# =============================================================================

log_section "Configuring Nginx"

rm -f /etc/nginx/sites-enabled/default

systemctl enable nginx
systemctl restart nginx

log_success "Nginx configured"

# =============================================================================
# FINAL STEPS
# =============================================================================

log_section "Setup Complete"

log_success "Server setup complete!"
log_info "Next steps:"
log_info "  1. Configure deploy/config/deploy.conf with your settings"
log_info "  2. Run deploy/scripts/deploy.sh to deploy the application"
log_info "  3. Your Tor onion address: $(cat /var/lib/tor/vault/hostname 2>/dev/null || echo 'Check /var/lib/tor/vault/hostname')"
