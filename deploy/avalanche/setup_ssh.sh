#!/bin/bash
# Setup SSH access to Avalanche server

echo "Setting up SSH access to Avalanche server..."

# Create key file
cat > ~/avalanche_key << 'EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACA2RgFm8IbN8PEne/JMVICr1UmUrFe0+0shOPn8xSCfOwAAAKA3rBdJN6wX
SQAAAAtzc2gtZWQyNTUxOQAAACA2RgFm8IbN8PEne/JMVICr1UmUrFe0+0shOPn8xSCfOw
AAAEA/1Kd8+UqEzK6/Rym4mbPPLkhEH+/AeFHguzMOzveBszZGAWbwhs3w8Sd78kxUgKvV
SZSsV7T7SyE4+fzFIJ87AAAAHGFnZW50MkBhcmNoaXRlY3QtbWFya2V0cGxhY2UB
-----END OPENSSH PRIVATE KEY-----
EOF

# Set permissions
chmod 600 ~/avalanche_key

# Add to SSH config
if ! grep -q "Host avalanche" ~/.ssh/config 2>/dev/null; then
    mkdir -p ~/.ssh
    cat >> ~/.ssh/config << 'EOF'

Host avalanche
    HostName 91.98.16.255
    User root
    IdentityFile ~/avalanche_key
    StrictHostKeyChecking no
    ServerAliveInterval 60
EOF
    echo "Added to ~/.ssh/config"
fi

echo "Setup complete!"
echo ""
echo "Test connection:"
echo "  ssh avalanche"
echo ""
echo "Or use directly:"
echo "  ssh -i ~/avalanche_key root@91.98.16.255"
