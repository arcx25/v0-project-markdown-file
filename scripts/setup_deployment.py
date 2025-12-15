#!/usr/bin/env python3
"""
Interactive Deployment Setup for ARCHITECT // VAULT
Runs in IDE to configure CI/CD pipeline to Avalanche server
"""

import os
import sys
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def generate_ssh_key_instructions():
    """Generate SSH key using pure Python"""
    print_section("Step 1: Generate SSH Key (Pure Python)")
    
    try:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        # Serialize public key
        public_ssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        ).decode('utf-8')
        
        # Save keys
        key_dir = Path.home() / ".ssh"
        key_dir.mkdir(exist_ok=True, mode=0o700)
        
        private_key_path = key_dir / "vault_deploy_key"
        public_key_path = key_dir / "vault_deploy_key.pub"
        
        # Write private key
        with open(private_key_path, 'w') as f:
            f.write(private_pem)
        private_key_path.chmod(0o600)
        
        # Write public key
        with open(public_key_path, 'w') as f:
            f.write(f"{public_ssh} vault-deploy-key\n")
        
        print(f"✓ SSH keys generated:")
        print(f"  Private: {private_key_path}")
        print(f"  Public:  {public_key_path}\n")
        
        return private_pem, f"{public_ssh} vault-deploy-key"
        
    except ImportError:
        print("✗ cryptography library not found")
        print("\nInstall it with:")
        print("  pip install cryptography\n")
        return None, None

def display_deployment_instructions(private_key, public_key):
    """Display step-by-step deployment instructions"""
    
    if not private_key or not public_key:
        print("✗ Keys not generated. Please install cryptography library.")
        return False
    
    print_section("Step 2: Add Public Key to Server")
    print("Copy this public key:\n")
    print(f"  {public_key}\n")
    print("Then SSH to your server and run:\n")
    print("  mkdir -p ~/.ssh")
    print(f"  echo '{public_key}' >> ~/.ssh/authorized_keys")
    print("  chmod 600 ~/.ssh/authorized_keys\n")
    
    input("Press Enter after adding the key to your server...")
    
    print_section("Step 3: Add to GitHub Secrets")
    print("Go to: GitHub Repository → Settings → Secrets → Actions\n")
    print("Add these secrets:\n")
    print("─" * 60)
    print("Name: SSH_PRIVATE_KEY")
    print("Value:")
    print(private_key)
    print("─" * 60)
    print("\nName: SERVER_HOST")
    print("Value: 91.98.16.255\n")
    print("Name: SERVER_USER")
    print("Value: avalanche\n")
    print("Name: SERVER_PORT")
    print("Value: 22\n")
    
    input("Press Enter after adding GitHub secrets...")
    
    print_section("Step 4: Deploy!")
    print("Method 1 - Automatic (GitHub Actions):")
    print("  git add .")
    print("  git commit -m 'Deploy ARCHITECT // VAULT'")
    print("  git push origin main\n")
    
    print("Method 2 - Manual (Run from IDE):")
    print("  python3 scripts/deploy_manual.py\n")
    
    return True

def main():
    """Main setup process"""
    print("\n" + "="*60)
    print("  ARCHITECT // VAULT - Pure Python Deployment Setup")
    print("="*60)
    print("\nThis script runs entirely in Python - no system tools needed!\n")
    
    private_key, public_key = generate_ssh_key_instructions()
    
    if private_key and public_key:
        display_deployment_instructions(private_key, public_key)
        
        print_section("Setup Complete!")
        print("✓ SSH keys generated")
        print("✓ Instructions displayed")
        print("\nYou can now deploy using:")
        print("  1. GitHub Actions (automatic)")
        print("  2. python3 scripts/deploy_manual.py (manual)\n")
    else:
        print("\n✗ Setup incomplete. Install dependencies:")
        print("  pip install cryptography paramiko\n")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
