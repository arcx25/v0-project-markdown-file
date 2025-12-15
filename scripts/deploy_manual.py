#!/usr/bin/env python3
"""
Manual Deployment Script - Pure Python
Deploy directly from IDE to Avalanche server using Paramiko
"""

import os
import sys
import io
import tarfile
from pathlib import Path

def print_status(message, status="info"):
    """Print formatted status message"""
    symbols = {"info": "→", "success": "✓", "error": "✗"}
    print(f"{symbols.get(status, '→')} {message}")

def create_deployment_package():
    """Create tar.gz of project files"""
    print_status("Creating deployment package...")
    
    # Files to exclude
    exclude_patterns = {
        '.git', '__pycache__', '*.pyc', '*.pyo', 
        '.env', 'venv', 'node_modules', '.DS_Store',
        '*.egg-info', '.pytest_cache', '.mypy_cache'
    }
    
    # Create in-memory tar.gz
    tar_buffer = io.BytesIO()
    
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        project_root = Path.cwd()
        
        for item in project_root.rglob('*'):
            # Skip excluded patterns
            if any(pattern in str(item) for pattern in exclude_patterns):
                continue
            
            if item.is_file():
                arcname = item.relative_to(project_root)
                tar.add(item, arcname=arcname)
    
    tar_buffer.seek(0)
    print_status("Deployment package created", "success")
    return tar_buffer

def deploy_to_server():
    """Deploy using paramiko (pure Python SSH)"""
    
    try:
        import paramiko
    except ImportError:
        print_status("paramiko not found. Install with: pip install paramiko", "error")
        sys.exit(1)
    
    # Configuration
    SERVER_HOST = os.getenv("SERVER_HOST", "91.98.16.255")
    SERVER_USER = os.getenv("SERVER_USER", "avalanche")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "22"))
    SSH_KEY_PATH = Path.home() / ".ssh" / "vault_deploy_key"
    
    print("\n" + "="*60)
    print("  ARCHITECT // VAULT - Manual Deployment")
    print("="*60)
    print(f"\nTarget: {SERVER_USER}@{SERVER_HOST}:{SERVER_PORT}")
    print(f"SSH Key: {SSH_KEY_PATH}\n")
    
    if not SSH_KEY_PATH.exists():
        print_status(f"SSH key not found: {SSH_KEY_PATH}", "error")
        print("\nRun setup first: python3 scripts/setup_deployment.py")
        sys.exit(1)
    
    response = input("Deploy now? (y/N): ").lower()
    if response != 'y':
        print("Deployment cancelled")
        return
    
    # Create package
    tar_buffer = create_deployment_package()
    
    # Connect to server
    print_status(f"Connecting to {SERVER_HOST}...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Load private key
        private_key = paramiko.Ed25519Key.from_private_key_file(str(SSH_KEY_PATH))
        
        ssh.connect(
            hostname=SERVER_HOST,
            port=SERVER_PORT,
            username=SERVER_USER,
            pkey=private_key,
            timeout=30
        )
        
        print_status("Connected to server", "success")
        
        # Upload deployment package
        print_status("Uploading deployment package...")
        sftp = ssh.open_sftp()
        
        with sftp.open('/tmp/vault_deploy.tar.gz', 'wb') as remote_file:
            remote_file.write(tar_buffer.read())
        
        sftp.close()
        print_status("Upload complete", "success")
        
        # Execute deployment commands
        print_status("Executing deployment on server...")
        
        deployment_script = """
set -e
echo "→ Extracting deployment package..."
sudo mkdir -p /opt/vault
sudo tar xzf /tmp/vault_deploy.tar.gz -C /opt/vault
cd /opt/vault

echo "→ Installing Python dependencies..."
sudo python3 -m pip install -r requirements.txt

echo "→ Running database migrations..."
sudo -u vault alembic upgrade head || echo "Migrations skipped"

echo "→ Restarting services..."
sudo systemctl restart vault-web vault-worker vault-beat || echo "Services not configured yet"

echo "✓ Deployment complete!"
sudo systemctl status vault-web --no-pager || echo "Check service status manually"
"""
        
        stdin, stdout, stderr = ssh.exec_command(deployment_script, get_pty=True)
        
        # Stream output
        for line in stdout:
            print(line.strip())
        
        # Check for errors
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print_status("Deployment successful!", "success")
        else:
            print_status(f"Deployment failed with exit code {exit_status}", "error")
            print("\nErrors:")
            for line in stderr:
                print(line.strip())
        
        ssh.close()
        
        print("\n" + "="*60)
        print("  Deployment Complete")
        print("="*60)
        print("\nNext steps:")
        print(f"  1. SSH to server: ssh {SERVER_USER}@{SERVER_HOST}")
        print("  2. Check status: sudo systemctl status vault-web")
        print("  3. View logs: sudo journalctl -u vault-web -f\n")
        
    except paramiko.AuthenticationException:
        print_status("Authentication failed. Check SSH key.", "error")
        sys.exit(1)
    except paramiko.SSHException as e:
        print_status(f"SSH error: {e}", "error")
        sys.exit(1)
    except Exception as e:
        print_status(f"Deployment failed: {e}", "error")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        deploy_to_server()
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(0)
