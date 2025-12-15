"""Input validation utilities."""
import re
from typing import Optional, List, Tuple


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """Validate username format."""
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 32:
        return False, "Username must be at most 32 characters"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    reserved = {
        'admin', 'administrator', 'root', 'system', 'support',
        'help', 'info', 'contact', 'security', 'moderator',
        'vault', 'architect', 'api', 'static', 'dashboard',
    }
    if username.lower() in reserved:
        return False, "This username is reserved"
    
    return True, None


def validate_pgp_key(key: str) -> Tuple[bool, Optional[str]]:
    """Basic PGP key format validation."""
    if not key:
        return False, "PGP public key is required"
    
    if "-----BEGIN PGP PUBLIC KEY BLOCK-----" not in key:
        return False, "Invalid PGP key format: missing BEGIN marker"
    
    if "-----END PGP PUBLIC KEY BLOCK-----" not in key:
        return False, "Invalid PGP key format: missing END marker"
    
    if len(key) < 200:
        return False, "PGP key appears to be too short"
    
    return True, None


def validate_challenge_response(response: str) -> Tuple[bool, Optional[str]]:
    """Validate challenge response format."""
    if not response:
        return False, "Challenge response is required"
    
    if not response.startswith("ARCHITECT_"):
        return False, "Invalid challenge format: must start with ARCHITECT_"
    
    parts = response.split("_")
    if len(parts) != 4:
        return False, "Invalid challenge format: expected 4 parts"
    
    return True, None


def sanitize_html(text: str) -> str:
    """Remove potentially dangerous HTML/script content."""
    if not text:
        return ""
    
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text


def validate_monero_address(address: str) -> Tuple[bool, Optional[str]]:
    """Basic Monero address validation."""
    if not address:
        return False, "Address is required"
    
    # Standard address (95 chars starting with 4)
    if len(address) == 95 and address.startswith('4'):
        return True, None
    
    # Integrated address (106 chars starting with 4)
    if len(address) == 106 and address.startswith('4'):
        return True, None
    
    # Subaddress (95 chars starting with 8)
    if len(address) == 95 and address.startswith('8'):
        return True, None
    
    return False, "Invalid Monero address format"


def check_pii_patterns(text: str) -> List[str]:
    """Check for potential PII patterns in text."""
    warnings = []
    
    if re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text):
        warnings.append("Text appears to contain an email address")
    
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\+\d{1,3}[-.\s]?\d{6,14}\b',
    ]
    for pattern in phone_patterns:
        if re.search(pattern, text):
            warnings.append("Text appears to contain a phone number")
            break
    
    if re.search(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b', text):
        warnings.append("Text appears to contain a Social Security Number")
    
    if re.search(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', text):
        warnings.append("Text appears to contain a credit card number")
    
    return warnings
