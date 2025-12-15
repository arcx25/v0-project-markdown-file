#!/bin/bash
set -e

echo "🚀 Setting up Vercel CI/CD for ARCHITECT // VAULT"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: ARCHITECT // VAULT"
fi

# Check for GitHub remote
if ! git remote | grep -q origin; then
    echo ""
    echo "⚠️  No GitHub remote found!"
    echo "Please create a GitHub repository and run:"
    echo ""
    echo "  git remote add origin https://github.com/YOUR_USERNAME/architect-vault.git"
    echo "  git push -u origin main"
    echo ""
    read -p "Press enter when you've created the repo and are ready to continue..."
fi

# Generate SSH key if needed
if [ ! -f ~/.ssh/id_ed25519 ]; then
    echo ""
    echo "🔑 Generating SSH key for deployment..."
    ssh-keygen -t ed25519 -C "deploy@architect-vault" -N "" -f ~/.ssh/id_ed25519
fi

echo ""
echo "📋 Next steps:"
echo ""
echo "1. Add these GitHub Secrets:"
echo "   https://github.com/YOUR_USERNAME/architect-vault/settings/secrets/actions"
echo ""
echo "   AVALANCHE_SERVER = 91.98.16.255"
echo "   AVALANCHE_USER = avalanche"
echo "   AVALANCHE_SSH_KEY = (paste the key below)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat ~/.ssh/id_ed25519
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "2. Copy public key to server:"
echo "   ssh-copy-id avalanche@91.98.16.255"
echo ""
echo "3. Connect repository to Vercel:"
echo "   https://vercel.com/new"
echo ""
echo "4. Push to deploy:"
echo "   git push origin main"
echo ""
echo "✅ Setup complete!"
