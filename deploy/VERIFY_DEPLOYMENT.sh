#!/bin/bash

# ARCHITECT // VAULT - Deployment Verification Script
# Runs comprehensive checks after deployment

set -e

echo "============================================================"
echo "  ARCHITECT // VAULT - Deployment Verification"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAILED++))
    fi
}

# 1. Check system services
echo "Checking system services..."
systemctl is-active --quiet postgresql && check "PostgreSQL running" || check "PostgreSQL running"
systemctl is-active --quiet redis && check "Redis running" || check "Redis running"
systemctl is-active --quiet tor && check "Tor running" || check "Tor running"
systemctl is-active --quiet nginx && check "Nginx running" || check "Nginx running"
echo ""

# 2. Check application services
echo "Checking application services..."
systemctl is-active --quiet vault-web && check "vault-web running" || check "vault-web running"
systemctl is-active --quiet vault-worker && check "vault-worker running" || check "vault-worker running"
systemctl is-active --quiet vault-beat && check "vault-beat running" || check "vault-beat running"
echo ""

# 3. Check database connection
echo "Checking database..."
sudo -u postgres psql -d vault -c "SELECT COUNT(*) FROM users;" > /dev/null 2>&1 && \
    check "Database accessible" || check "Database accessible"
echo ""

# 4. Check Redis connection
echo "Checking Redis..."
redis-cli ping > /dev/null 2>&1 && check "Redis responding" || check "Redis responding"
echo ""

# 5. Check Tor hidden service
echo "Checking Tor..."
if [ -f /var/lib/tor/vault/hostname ]; then
    ONION=$(cat /var/lib/tor/vault/hostname)
    check "Tor onion address: $ONION"
else
    check "Tor onion address"
fi
echo ""

# 6. Check application health
echo "Checking application health..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$HTTP_CODE" = "200" ]; then
    check "Application health endpoint"
else
    check "Application health endpoint (got HTTP $HTTP_CODE)"
fi
echo ""

# 7. Check Monero services
echo "Checking Monero..."
systemctl is-active --quiet monerod && check "Monero daemon running" || echo -e "${YELLOW}⚠${NC} Monero daemon not running (optional)"
systemctl is-active --quiet monero-wallet-rpc && check "Monero wallet RPC running" || echo -e "${YELLOW}⚠${NC} Monero wallet RPC not running (configure later)"
echo ""

# 8. Check log files
echo "Checking logs..."
[ -f /var/log/vault/app.log ] && check "Application log file exists" || check "Application log file exists"
[ -s /var/log/vault/app.log ] && check "Application log has content" || echo -e "${YELLOW}⚠${NC} Application log is empty (just started?)"
echo ""

# 9. Check file permissions
echo "Checking permissions..."
[ -d /opt/vault ] && [ -r /opt/vault ] && check "/opt/vault directory accessible" || check "/opt/vault directory accessible"
[ -d /var/lib/vault/gpg ] && check "GPG home directory exists" || check "GPG home directory exists"
echo ""

# 10. Check API endpoints
echo "Checking API endpoints..."
curl -s http://localhost:8000/api/auth/challenge -H "Content-Type: application/json" -d '{"username":"test"}' > /dev/null 2>&1
check "API auth endpoint responding"
echo ""

# Summary
echo "============================================================"
echo "  Verification Summary"
echo "============================================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Deployment successful.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Create admin user: python3 /opt/vault/scripts/init_admin.py"
    echo "2. Access your onion address: http://$ONION"
    echo "3. Test registration and login"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Review errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "- Check service logs: journalctl -u vault-web"
    echo "- Verify .env file: cat /opt/vault/.env"
    echo "- Check database: sudo -u postgres psql -d vault"
    exit 1
fi
