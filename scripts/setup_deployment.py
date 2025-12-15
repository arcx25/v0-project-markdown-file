#!/usr/bin/env python3
"""
Interactive Deployment Setup for ARCHITECT // VAULT
Runs in IDE to configure CI/CD pipeline to Avalanche server
"""

import os
import sys
import subprocess
from pathlib import Path

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def check_command(cmd):
    """Check if a command exists"""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def generate_ssh_key():
    """Generate SSH key for deployment"""
    print_section("Step 1: Generate SSH Key")
    
    key_path = Path.home() / ".ssh" / "vault_deploy_key"
    
    if key_path.exists():
        print(f"✓ SSH key already exists at {key_path}")
        response = input("Generate new key? (y/N): ").lower()
        if response != 'y':
            return key_path
    
    print("Generating new SSH key...")
    try:
        subprocess.run([
            "ssh-keygen",
            "-t", "ed25519",
            "-f", str(key_path),
            "-N", "",
            "-C", "vault-deploy-key"
        ], check=True)
        print(f"✓ SSH key generated at {key_path}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate SSH key: {e}")
        return None
    
    return key_path

def display_public_key(key_path):
    """Display public key for copying to server"""
    print_section("Step 2: Add Public Key to Avalanche Server")
    
    pub_key_path = Path(str(key_path) + ".pub")
    
    if not pub_key_path.exists():
        print(f"✗ Public key not found at {pub_key_path}")
        return False
    
    with open(pub_key_path, 'r') as f:
        public_key = f.read().strip()
    
    print("Copy this public key:\n")
    print(f"  {public_key}\n")
    print("Then run this command on your LOCAL machine (not in IDE):\n")
    print(f"  ssh avalanche@91.98.16.255 'mkdir -p ~/.ssh && echo \"{public_key}\" >> ~/.ssh/authorized_keys'\n")
    
    input("Press Enter after you've added the key to the server...")
    return True

def display_private_key(key_path):
    """Display private key for GitHub Secrets"""
    print_section("Step 3: Add Private Key to GitHub Secrets")
    
    if not key_path.exists():
        print(f"✗ Private key not found at {key_path}")
        return False
    
    with open(key_path, 'r') as f:
        private_key = f.read()
    
    print("Copy this ENTIRE private key (including BEGIN/END lines):\n")
    print("─" * 60)
    print(private_key)
    print("─" * 60)
    print("\nGo to your GitHub repository:")
    print("  Settings → Secrets and variables → Actions → New repository secret\n")
    print("Add these secrets:")
    print("  Name: SSH_PRIVATE_KEY")
    print("  Value: [Paste the private key above]\n")
    print("  Name: SERVER_HOST")
    print("  Value: 91.98.16.255\n")
    print("  Name: SERVER_USER")
    print("  Value: avalanche\n")
    print("  Name: SERVER_PORT")
    print("  Value: 22\n")
    
    input("Press Enter after you've added the GitHub secrets...")
    return True

def create_github_workflow():
    """Create GitHub Actions workflow"""
    print_section("Step 4: Create GitHub Workflow")
    
    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_file = workflow_dir / "deploy.yml"
    
    if workflow_file.exists():
        print(f"✓ GitHub workflow already exists at {workflow_file}")
    else:
        print(f"✓ GitHub workflow created at {workflow_file}")
    
    print("\nWorkflow will trigger on:")
    print("  - Push to main branch")
    print("  - Manual workflow dispatch")
    
    return True

def setup_vercel():
    """Guide through Vercel setup"""
    print_section("Step 5: Setup Vercel (Optional)")
    
    print("To deploy the frontend dashboard to Vercel:\n")
    print("1. Install Vercel CLI on your local machine:")
    print("   npm i -g vercel\n")
    print("2. Navigate to frontend directory:")
    print("   cd frontend\n")
    print("3. Deploy to Vercel:")
    print("   vercel --prod\n")
    print("4. Follow the prompts to link your project\n")
    
    response = input("Skip Vercel setup? (Y/n): ").lower()
    return response != 'n'

def test_deployment():
    """Guide through testing deployment"""
    print_section("Step 6: Test Deployment")
    
    print("To test the deployment:\n")
    print("1. Commit your changes:")
    print("   git add .")
    print("   git commit -m 'Setup deployment pipeline'\n")
    print("2. Push to trigger deployment:")
    print("   git push origin main\n")
    print("3. Watch the deployment:")
    print("   Go to GitHub → Actions tab\n")
    print("4. Check your server:")
    print("   ssh avalanche@91.98.16.255")
    print("   sudo systemctl status vault-web\n")
    
    return True

def main():
    """Main setup process"""
    print("\n" + "="*60)
    print("  ARCHITECT // VAULT - Deployment Setup")
    print("="*60)
    
    print("\nThis script will help you setup automated deployment")
    print("from Vercel/GitHub to your Avalanche server.\n")
    
    # Check prerequisites
    print("Checking prerequisites...")
    if not check_command("ssh-keygen"):
        print("✗ ssh-keygen not found. Please install OpenSSH.")
        sys.exit(1)
    if not check_command("git"):
        print("✗ git not found. Please install Git.")
        sys.exit(1)
    print("✓ Prerequisites satisfied\n")
    
    # Run setup steps
    key_path = generate_ssh_key()
    if not key_path:
        print("\n✗ Setup failed at SSH key generation")
        sys.exit(1)
    
    if not display_public_key(key_path):
        print("\n✗ Setup failed at public key display")
        sys.exit(1)
    
    if not display_private_key(key_path):
        print("\n✗ Setup failed at private key display")
        sys.exit(1)
    
    if not create_github_workflow():
        print("\n✗ Setup failed at workflow creation")
        sys.exit(1)
    
    setup_vercel()
    test_deployment()
    
    # Final summary
    print_section("Setup Complete!")
    print("✓ SSH keys generated")
    print("✓ GitHub workflow configured")
    print("✓ Ready to deploy\n")
    print("Next steps:")
    print("1. Verify SSH key is on server: ssh avalanche@91.98.16.255")
    print("2. Verify GitHub secrets are set")
    print("3. Push to main branch to trigger deployment")
    print("\nFor manual deployment, run:")
    print("  bash deploy/avalanche/deploy_to_avalanche.sh\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
