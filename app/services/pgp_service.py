"""PGP cryptographic operations service."""

import gnupg
import secrets
import hashlib
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, List

from app.config import get_settings


class PGPKeyAlgorithm(Enum):
    """Supported PGP key algorithms with security ratings."""
    ED25519 = "ed25519"  # Preferred - modern ECC
    CURVE25519 = "curve25519"  # Acceptable - modern ECC
    RSA4096 = "rsa4096"  # Acceptable - strong RSA
    RSA2048 = "rsa2048"  # REJECTED - too weak
    DSA = "dsa"  # REJECTED - deprecated


@dataclass
class PGPKeyInfo:
    """Validated PGP key information with security assessment."""
    fingerprint: str
    algorithm: PGPKeyAlgorithm
    key_length: int
    user_ids: List[str]
    expires_at: Optional[int]
    is_revoked: bool
    is_valid: bool
    rejection_reason: Optional[str] = None


class PGPService:
    """
    Advanced PGP cryptographic operations service.
    
    Features:
    - Strict key validation (Ed25519, Curve25519, RSA4096+)
    - ARCHITECT protocol challenge-response authentication
    - End-to-end message encryption
    - Platform message signing
    - Comprehensive security checks
    """
    
    def __init__(self):
        settings = get_settings()
        self.gpg = gnupg.GPG(gnupghome=settings.GPG_HOME_DIR)
        self.gpg.encoding = "utf-8"
        self.settings = settings
    
    def validate_public_key(self, armored_key: str) -> PGPKeyInfo:
        """
        Validate PGP public key with strict security requirements.
        
        ACCEPTS:
        - Ed25519 (preferred - modern elliptic curve)
        - Curve25519 (acceptable - modern elliptic curve)
        - RSA 4096+ (acceptable - strong traditional)
        
        REJECTS:
        - DSA (any length - deprecated algorithm)
        - RSA < 4096 (weak key length)
        - Expired or near-expiry keys (< 30 days)
        - Revoked keys
        
        Args:
            armored_key: ASCII-armored PGP public key block
            
        Returns:
            PGPKeyInfo with validation status and details
        """
        # Import key into temporary keyring
        import_result = self.gpg.import_keys(armored_key)
        
        if not import_result.fingerprints:
            return PGPKeyInfo(
                fingerprint="",
                algorithm=PGPKeyAlgorithm.RSA2048,
                key_length=0,
                user_ids=[],
                expires_at=None,
                is_revoked=False,
                is_valid=False,
                rejection_reason="Invalid PGP key format - could not parse key block",
            )
        
        fingerprint = import_result.fingerprints[0]
        keys = self.gpg.list_keys(keys=[fingerprint])
        
        if not keys:
            self._cleanup_key(fingerprint)
            return PGPKeyInfo(
                fingerprint=fingerprint,
                algorithm=PGPKeyAlgorithm.RSA2048,
                key_length=0,
                user_ids=[],
                expires_at=None,
                is_revoked=False,
                is_valid=False,
                rejection_reason="Could not retrieve key details after import",
            )
        
        key = keys[0]
        
        algo = key.get("algo", "").lower()
        key_length = int(key.get("length", 0))
        
        # GPG algorithm codes: 1=RSA, 17=DSA, 22=EdDSA/Ed25519
        if "ed25519" in algo or key.get("algo") == "22":
            algorithm = PGPKeyAlgorithm.ED25519
        elif "cv25519" in algo or "curve25519" in algo:
            algorithm = PGPKeyAlgorithm.CURVE25519
        elif "rsa" in algo or key.get("algo") in ["1", "2", "3"]:
            algorithm = PGPKeyAlgorithm.RSA4096 if key_length >= 4096 else PGPKeyAlgorithm.RSA2048
        elif "dsa" in algo or key.get("algo") == "17":
            algorithm = PGPKeyAlgorithm.DSA
        else:
            algorithm = PGPKeyAlgorithm.RSA2048
        
        # Check expiration
        expires_at = None
        if key.get("expires"):
            try:
                expires_at = int(key["expires"])
            except (ValueError, TypeError):
                pass
        
        # Check revocation
        is_revoked = key.get("trust", "") == "r"
        
        rejection_reason = None
        is_valid = True
        
        if algorithm == PGPKeyAlgorithm.DSA:
            is_valid = False
            rejection_reason = "DSA keys are not accepted due to known security vulnerabilities. Please use Ed25519 or RSA-4096+."
        elif algorithm == PGPKeyAlgorithm.RSA2048:
            is_valid = False
            rejection_reason = f"RSA keys must be at least 4096 bits for adequate security. Your key is {key_length} bits."
        elif is_revoked:
            is_valid = False
            rejection_reason = "This key has been revoked and cannot be used for authentication."
        elif expires_at and expires_at < time.time() + (30 * 24 * 60 * 60):
            is_valid = False
            rejection_reason = "Key expires within 30 days. Please use a longer-lived key for account security."
        
        # Clean up invalid keys from keyring
        if not is_valid:
            self._cleanup_key(fingerprint)
        
        return PGPKeyInfo(
            fingerprint=fingerprint,
            algorithm=algorithm,
            key_length=key_length,
            user_ids=key.get("uids", []),
            expires_at=expires_at,
            is_revoked=is_revoked,
            is_valid=is_valid,
            rejection_reason=rejection_reason,
        )
    
    def generate_challenge(self, username: str) -> Tuple[str, str]:
        """
        Generate ARCHITECT protocol challenge for authentication.
        
        Format: ARCHITECT_{token}_{timestamp}_{server_fingerprint_short}
        
        Args:
            username: Username for audit logging
            
        Returns:
            Tuple of (challenge_plaintext, challenge_sha256_hash)
        """
        # Generate 384 bits of cryptographic entropy
        token = secrets.token_urlsafe(48)
        timestamp = int(time.time())
        server_fp_short = self.settings.PLATFORM_PGP_FINGERPRINT[:8].upper()
        
        challenge = f"ARCHITECT_{token}_{timestamp}_{server_fp_short}"
        challenge_hash = hashlib.sha256(challenge.encode()).hexdigest()
        
        return challenge, challenge_hash
    
    def encrypt_challenge(self, challenge: str, recipient_fingerprint: str) -> str:
        """
        Encrypt challenge to user's public key.
        
        Args:
            challenge: Plaintext challenge string
            recipient_fingerprint: User's PGP key fingerprint
            
        Returns:
            ASCII-armored PGP encrypted message
            
        Raises:
            ValueError: If encryption fails
        """
        encrypted = self.gpg.encrypt(
            challenge,
            recipients=[recipient_fingerprint],
            armor=True,
            always_trust=True,
        )
        
        if not encrypted.ok:
            raise ValueError(f"PGP encryption failed: {encrypted.status}")
        
        return str(encrypted)
    
    def verify_challenge_response(
        self,
        response: str,
        expected_hash: str,
        max_age_seconds: int = 300,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify ARCHITECT protocol challenge response with timing-safe comparison.
        
        Validates:
        - Format (ARCHITECT_{token}_{timestamp}_{server_fp})
        - Hash matches (constant-time comparison)
        - Timestamp within window
        - Server fingerprint matches
        
        Args:
            response: Decrypted challenge from user
            expected_hash: SHA-256 of original challenge
            max_age_seconds: Max challenge age (default 300s)
            
        Returns:
            Tuple of (is_valid, error_message_or_none)
        """
        # Validate format
        parts = response.split("_")
        if len(parts) != 4:
            return False, "Invalid challenge format: expected 4 underscore-separated parts"
        
        if parts[0] != "ARCHITECT":
            return False, "Invalid challenge format: must start with 'ARCHITECT'"
        
        response_hash = hashlib.sha256(response.encode()).hexdigest()
        if not secrets.compare_digest(response_hash, expected_hash):
            return False, "Challenge response does not match expected value"
        
        # Validate timestamp with clock skew tolerance
        try:
            timestamp = int(parts[2])
            age = time.time() - timestamp
            
            if age > max_age_seconds:
                return False, f"Challenge has expired (age: {int(age)}s, max: {max_age_seconds}s)"
            if age < -60:  # 60s clock skew tolerance
                return False, "Challenge timestamp is in the future - check system clock"
        except ValueError:
            return False, "Invalid timestamp in challenge response"
        
        # Validate server fingerprint
        expected_fp = self.settings.PLATFORM_PGP_FINGERPRINT[:8].upper()
        if parts[3].upper() != expected_fp:
            return False, "Server fingerprint mismatch - possible tampering detected"
        
        return True, None
    
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
    
    def hash_challenge(self, challenge: str) -> str:
        """Create a secure hash of a challenge for storage."""
        return hashlib.sha256(challenge.encode()).hexdigest()
    
    def encrypt_message(
        self,
        plaintext: str,
        recipient_fingerprint: str,
        sign: bool = True,
    ) -> str:
        """
        Encrypt message for secure vendor-buyer communication.
        
        Args:
            plaintext: Message content
            recipient_fingerprint: Recipient's PGP fingerprint
            sign: Whether to sign with platform key
            
        Returns:
            ASCII-armored encrypted message
        """
        kwargs = {
            "recipients": [recipient_fingerprint],
            "armor": True,
            "always_trust": True,
        }
        
        if sign:
            kwargs["sign"] = self.settings.PLATFORM_PGP_FINGERPRINT
            kwargs["passphrase"] = self.settings.PLATFORM_PGP_PASSPHRASE
        
        encrypted = self.gpg.encrypt(plaintext, **kwargs)
        
        if not encrypted.ok:
            raise ValueError(f"PGP encryption failed: {encrypted.status}")
        
        return str(encrypted)
    
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
    
    def _cleanup_key(self, fingerprint: str) -> bool:
        """Remove key from keyring after validation."""
        try:
            self.gpg.delete_keys(fingerprint)
            return True
        except Exception:
            return False


# Singleton instance
pgp_service = PGPService()
