#!/usr/bin/env python3
"""
ARCHITECT // VAULT - Platform PGP Key Generator

Generates the platform's master PGP keypair for signing challenges and verifying users.
This should be run ONCE during initial deployment.

Usage:
    python3 scripts/generate_platform_keys.py

The generated keys will be saved to:
    - /var/lib/vault/gnupg/platform_private.asc (KEEP SECURE!)
    - /var/lib/vault/gnupg/platform_public.asc (distribute to users)
"""

import os
import sys
import secrets
import gnupg
from pathlib import Path

# Configuration
GNUPG_HOME = os.getenv('GNUPG_HOME', '/var/lib/vault/gnupg')
KEY_TYPE = 'RSA'
KEY_LENGTH = 4096
NAME = 'ARCHITECT VAULT Platform'
EMAIL = 'platform@architect-vault.local'
PASSPHRASE_LENGTH = 32


def generate_secure_passphrase(length: int = 32) -> str:
    """Generate a cryptographically secure passphrase."""
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    print("=" * 80)
    print("ARCHITECT // VAULT - Platform Key Generator")
    print("=" * 80)
    print()
    
    # Create GNUPG home if it doesn't exist
    gnupg_path = Path(GNUPG_HOME)
    gnupg_path.mkdir(parents=True, exist_ok=True)
    os.chmod(GNUPG_HOME, 0o700)
    
    print(f"[+] Using GNUPG home: {GNUPG_HOME}")
    
    # Initialize GPG
    gpg = gnupg.GPG(gnupghome=GNUPG_HOME)
    
    # Check if platform key already exists
    keys = gpg.list_keys()
    platform_key = next((k for k in keys if EMAIL in k.get('uids', [''])[0]), None)
    
    if platform_key:
        print(f"[!] Platform key already exists: {platform_key['fingerprint']}")
        response = input("Do you want to regenerate? This will DELETE the existing key! (yes/no): ")
        if response.lower() != 'yes':
            print("[*] Keeping existing key. Exiting.")
            return
        
        # Delete existing key
        gpg.delete_keys(platform_key['fingerprint'], True)  # Delete private key
        gpg.delete_keys(platform_key['fingerprint'])  # Delete public key
        print("[+] Deleted existing key")
    
    # Generate passphrase
    passphrase = generate_secure_passphrase(PASSPHRASE_LENGTH)
    
    print(f"\n[+] Generating {KEY_LENGTH}-bit {KEY_TYPE} keypair...")
    print(f"    Name: {NAME}")
    print(f"    Email: {EMAIL}")
    print()
    
    # Generate key
    input_data = gpg.gen_key_input(
        key_type=KEY_TYPE,
        key_length=KEY_LENGTH,
        name_real=NAME,
        name_email=EMAIL,
        passphrase=passphrase,
        expire_date='0'  # Never expire
    )
    
    key = gpg.gen_key(input_data)
    
    if not key:
        print("[!] ERROR: Key generation failed!")
        sys.exit(1)
    
    print(f"[+] Key generated successfully!")
    print(f"    Fingerprint: {key}")
    
    # Export keys
    private_key_path = gnupg_path / 'platform_private.asc'
    public_key_path = gnupg_path / 'platform_public.asc'
    passphrase_path = gnupg_path / 'platform_passphrase.txt'
    
    # Export private key
    private_key = gpg.export_keys(str(key), True, passphrase=passphrase)
    with open(private_key_path, 'w') as f:
        f.write(private_key)
    os.chmod(private_key_path, 0o600)
    print(f"[+] Private key saved to: {private_key_path}")
    
    # Export public key
    public_key = gpg.export_keys(str(key))
    with open(public_key_path, 'w') as f:
        f.write(public_key)
    os.chmod(public_key_path, 0o644)
    print(f"[+] Public key saved to: {public_key_path}")
    
    # Save passphrase
    with open(passphrase_path, 'w') as f:
        f.write(passphrase)
    os.chmod(passphrase_path, 0o600)
    print(f"[+] Passphrase saved to: {passphrase_path}")
    
    print()
    print("=" * 80)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 80)
    print()
    print(f"1. BACKUP the private key: {private_key_path}")
    print(f"2. BACKUP the passphrase: {passphrase_path}")
    print("3. Store backups in a secure, encrypted location")
    print("4. Never commit these files to version control")
    print(f"5. Distribute the public key: {public_key_path}")
    print()
    print("Add to your .env file:")
    print(f"PGP_PRIVATE_KEY_PATH={private_key_path}")
    print(f"PGP_PUBLIC_KEY_PATH={public_key_path}")
    print(f"PGP_PASSPHRASE={passphrase}")
    print()
    print("Platform key generation complete!")
    print("=" * 80)


if __name__ == '__main__':
    main()
