"""Text and data formatting utilities."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import re


def format_xmr(atomic_units: int) -> str:
    """Format atomic units to XMR display string."""
    xmr = Decimal(atomic_units) / Decimal(1e12)
    return f"{xmr:.6f}"


def format_xmr_full(atomic_units: int) -> str:
    """Format atomic units to full precision XMR."""
    xmr = Decimal(atomic_units) / Decimal(1e12)
    return f"{xmr:.12f}"


def format_usd(cents: int) -> str:
    """Format cents to USD display string."""
    dollars = Decimal(cents) / 100
    return f"${dollars:.2f}"


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string."""
    if not dt:
        return ""
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    if seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    if diff.days < 7:
        return f"{diff.days}d ago"
    if diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks}w ago"
    if diff.days < 365:
        months = diff.days // 30
        return f"{months}mo ago"
    
    years = diff.days // 365
    return f"{years}y ago"


def format_date(dt: datetime) -> str:
    """Format datetime as readable date."""
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y")


def format_datetime_full(dt: datetime) -> str:
    """Format datetime as full date and time."""
    if not dt:
        return ""
    return dt.strftime("%B %d, %Y at %H:%M UTC")


def generate_slug(text: str, max_length: int = 200) -> str:
    """Generate URL-safe slug from text."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug[:max_length]


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to max length, preserving word boundaries."""
    if not text or len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    if last_space > max_length // 2:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def mask_fingerprint(fingerprint: str, show_chars: int = 8) -> str:
    """Mask a PGP fingerprint for display."""
    if not fingerprint:
        return ""
    if len(fingerprint) <= show_chars * 2:
        return fingerprint
    return f"{fingerprint[:show_chars]}...{fingerprint[-show_chars:]}"
