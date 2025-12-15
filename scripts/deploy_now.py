#!/usr/bin/env python3
"""
Quick Deploy Script - Deploy immediately to Avalanche server
Runs in IDE or local machine
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {description} completed")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("="*60)
    print("  ARCHITECT // VAULT - Quick Deploy")
    print("="*60)
    
    # Configuration
    SERVER_USER = os.getenv("SERVER_USER", "avalanche")
    SERVER_HOST = os.getenv("SERVER_HOST", "91.98.16.255")
    SERVER_PORT = os.getenv("SERVER_PORT", "22")
    SSH_KEY = os.getenv("SSH_PRIVATE_KEY_PATH", str(Path.home() / ".ssh" / "vault_deploy_key"))
    
    print(f"\nTarget: {SERVER_USER}@{SERVER_HOST}:{SERVER_PORT}")
    print(f"SSH Key: {SSH_KEY}\n")
    
    response = input("Deploy now? (y/N): ").lower()
    if response != 'y':
        print("Deployment cancelled")
        sys.exit(0)
    
    # Create deployment package
    if not run_command(
        "tar czf /tmp/vault_deploy.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' .",
        "Creating deployment package"
    ):
        sys.exit(1)
    
    # Upload to server
    scp_cmd = f"scp -i {SSH_KEY} -P {SERVER_PORT} /tmp/vault_deploy.tar.gz {SERVER_USER}@{SERVER_HOST}:/tmp/"
    if not run_command(scp_cmd, "Uploading to server"):
        sys.exit(1)
    
    # Execute deployment on server
    ssh_cmd = f"""ssh -i {SSH_KEY} -p {SERVER_PORT} {SERVER_USER}@{SERVER_HOST} 'bash -s' << 'ENDSSH'
set -e
echo "→ Extracting deployment package..."
sudo mkdir -p /opt/vault
sudo tar xzf /tmp/vault_deploy.tar.gz -C /opt/vault
cd /opt/vault

echo "→ Installing Python dependencies..."
sudo python3 -m pip install -r requirements.txt

echo "→ Running database migrations..."
sudo -u vault alembic upgrade head

echo "→ Restarting services..."
sudo systemctl restart vault-web vault-worker vault-beat

echo "✓ Deployment complete!"
sudo systemctl status vault-web --no-pager
ENDSSH
"""
    
    if not run_command(ssh_cmd, "Deploying on server"):
        sys.exit(1)
    
    # Cleanup
    run_command("rm /tmp/vault_deploy.tar.gz", "Cleaning up")
    
    print("\n" + "="*60)
    print("  Deployment Successful!")
    print("="*60)
    print("\nCheck status:")
    print(f"  ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_HOST} 'sudo systemctl status vault-web'")
    print("\nView logs:")
    print(f"  ssh -i {SSH_KEY} {SERVER_USER}@{SERVER_HOST} 'sudo journalctl -u vault-web -f'")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Deployment failed: {e}")
        sys.exit(1)
