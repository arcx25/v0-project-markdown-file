#!/bin/bash
# Health check script for monitoring

set -euo pipefail

ERRORS=0

# Check web service
if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✓ Web service: HEALTHY"
else
    echo "✗ Web service: NOT RESPONDING"
    ((ERRORS++))
fi

# Check systemd services
for service in vault-web vault-worker vault-beat; do
    if systemctl is-active --quiet $service; then
        echo "✓ $service: RUNNING"
    else
        echo "✗ $service: NOT RUNNING"
        ((ERRORS++))
    fi
done

# Check PostgreSQL
if sudo -u postgres psql -c "SELECT 1" vault > /dev/null 2>&1; then
    echo "✓ PostgreSQL: CONNECTED"
else
    echo "✗ PostgreSQL: CONNECTION FAILED"
    ((ERRORS++))
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis: RESPONDING"
else
    echo "✗ Redis: NOT RESPONDING"
    ((ERRORS++))
fi

# Check Tor
if [ -f /var/lib/tor/vault/hostname ]; then
    ONION=$(cat /var/lib/tor/vault/hostname)
    echo "✓ Tor: $ONION"
else
    echo "✗ Tor: NO ONION ADDRESS"
    ((ERRORS++))
fi

# Check disk space
DISK_USAGE=$(df -h /var/lib/vault | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo "✓ Disk space: ${DISK_USAGE}% used"
else
    echo "⚠ Disk space: ${DISK_USAGE}% used (HIGH)"
    ((ERRORS++))
fi

# Exit with error count
exit $ERRORS
