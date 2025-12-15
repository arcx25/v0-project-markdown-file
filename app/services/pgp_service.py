"""PGP cryptographic operations service."""

import gnupg
import secrets
import hashlib
from typing import Optional, Tuple
from datetime import datetime, timezone

from app.config import get_settings


class PGPService:
    """Service for PGP operations using GnuPG."""
    
    def __init__(self):
        settings = get_settings()
        self.gpg = gnupg.GPG(
            gnupghome=settings.GPG_HOME_DIR,
            gpgbinary=settings.GPG_BINARY
        )
        self.challenge_length = settings.CHALLENGE_LENGTH
    
    def import_public_key(self, public_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Import a PGP public key.
        
        Returns:
            Tuple of (success, fingerprint, error_message)
        """
        try:
            result = self.gpg.import_keys(public_key)
            
            if not result.fingerprints:
                return False, None, "Invalid PGP key format"
            
            fingerprint = result.fingerprints[0]
            
            # Verify the key was imported
            keys = self.gpg.list_keys(keys=fingerprint)
            if not keys:
                return False, None, "Key import verification failed"
            
            return True, fingerprint, None
            
        except Exception as e:
            return False, None, f"Key import error: {str(e)}"
    
    def verify_key_ownership(self, fingerprint: str, signed_challenge: str, original_challenge: str) -> bool:
        """
        Verify that a signed challenge was created by the owner of the key.
        
        Args:
            fingerprint: PGP key fingerprint
            signed_challenge: ASCII-armored signed message
            original_challenge: Original challenge text
            
        Returns:
            True if signature is valid and matches fingerprint
        """
        try:
            verified = self.gpg.verify(signed_challenge)
            
            if not verified.valid:
                return False
            
            # Check fingerprint matches
            if verified.fingerprint.upper() != fingerprint.upper():
                return False
            
            # Extract the signed text and verify it matches challenge
            # For clearsigned messages, the original text is preserved
            decrypted = self.gpg.decrypt(signed_challenge)
            if not decrypted.ok:
                # Try to extract from clearsigned format
                lines = signed_challenge.split('\n')
                try:
                    start_idx = lines.index('-----BEGIN PGP SIGNED MESSAGE-----')
                    hash_header_idx = start_idx + 1
                    # Skip to blank line after headers
                    blank_idx = hash_header_idx + 1
                    while blank_idx < len(lines) and lines[blank_idx].strip():
                        blank_idx += 1
                    
                    # Get message content
                    end_idx = lines.index('-----BEGIN PGP SIGNATURE-----')
                    message_lines = lines[blank_idx + 1:end_idx]
                    extracted_message = '\n'.join(message_lines).strip()
                    
                    return extracted_message == original_challenge
                except (ValueError, IndexError):
                    return False
            
            return str(decrypted).strip() == original_challenge.strip()
            
        except Exception as e:
            print(f"[v0] PGP verification error: {e}")
            return False
    
    def generate_challenge(self) -> str:
        """Generate a random challenge string."""
        return secrets.token_urlsafe(self.challenge_length)
    
    def hash_challenge(self, challenge: str) -> str:
        """Create a secure hash of a challenge for storage."""
        return hashlib.sha256(challenge.encode()).hexdigest()
    
    def encrypt_message(self, message: str, recipient_fingerprint: str) -> Optional[str]:
        """
        Encrypt a message for a specific recipient.
        
        Args:
            message: Plaintext message
            recipient_fingerprint: Recipient's PGP fingerprint
            
        Returns:
            ASCII-armored encrypted message or None on failure
        """
        try:
            encrypted = self.gpg.encrypt(
                message,
                recipient_fingerprint,
                always_trust=True,  # We manage trust separately
                armor=True
            )
            
            if not encrypted.ok:
                return None
            
            return str(encrypted)
            
        except Exception as e:
            print(f"[v0] PGP encryption error: {e}")
            return None
    
    def decrypt_message(self, encrypted_message: str) -> Optional[str]:
        """
        Decrypt a message (requires private key in keyring).
        
        Args:
            encrypted_message: ASCII-armored encrypted message
            
        Returns:
            Decrypted plaintext or None on failure
        """
        try:
            decrypted = self.gpg.decrypt(encrypted_message)
            
            if not decrypted.ok:
                return None
            
            return str(decrypted)
            
        except Exception as e:
            print(f"[v0] PGP decryption error: {e}")
            return None
    
    def get_key_info(self, fingerprint: str) -> Optional[dict]:
        """Get information about a key in the keyring."""
        try:
            keys = self.gpg.list_keys(keys=fingerprint)
            if keys:
                return {
                    "fingerprint": keys[0]["fingerprint"],
                    "uids": keys[0].get("uids", []),
                    "length": keys[0].get("length"),
                    "algo": keys[0].get("algo"),
                    "created": keys[0].get("date"),
                    "expires": keys[0].get("expires"),
                }
            return None
        except Exception:
            return None
