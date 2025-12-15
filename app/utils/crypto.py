"""Cryptographic utility functions."""
import hashlib
import secrets
import hmac
from typing import Tuple


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return secrets.compare_digest(a, b)


def generate_csrf_token(session_token: str, secret_key: str) -> str:
    """Generate CSRF token tied to session."""
    random_part = secrets.token_hex(16)
    message = f"{session_token}:{random_part}"
    signature = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
    return f"{random_part}:{signature}"


def verify_csrf_token(csrf_token: str, session_token: str, secret_key: str) -> bool:
    """Verify CSRF token."""
    try:
        random_part, signature = csrf_token.split(":", 1)
        message = f"{session_token}:{random_part}"
        expected_signature = hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()[:32]
        return constant_time_compare(signature, expected_signature)
    except (ValueError, AttributeError):
        return False


def generate_payment_id() -> str:
    """Generate a random 8-byte payment ID for Monero."""
    return secrets.token_hex(8)


def hash_content(content: str) -> str:
    """Hash content for integrity verification."""
    return hashlib.sha256(content.encode()).hexdigest()
