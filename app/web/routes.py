"""Web frontend routes - Server-side rendered marketplace."""

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
import hashlib

from app.database import get_db
from app.dependencies import get_current_user_optional, get_current_user, require_role, get_redis
from app.models.user import User, UserRole
from app.models.lead import Lead, LeadStatus, LeadInterest, InterestStatus
from app.models.listing import SupportListing, ListingStatus, SupportTier
from app.models.message import Conversation, Message
from app.services.auth_service import AuthService, AuthenticationError
from app.services.lead_service import LeadService
from app.services.listing_service import ListingService
from app.services.message_service import MessageService
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def nl2br(value: str) -> str:
    """Convert newlines to <br> tags."""
    if not value:
        return ""
    import markupsafe
    return markupsafe.Markup(value.replace('\n', '<br>\n'))


def format_date(value) -> str:
    """Format datetime to readable date."""
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value.strftime("%B %d, %Y")


def format_datetime(value) -> str:
    """Format datetime to readable date and time."""
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value.strftime("%B %d, %Y at %H:%M UTC")


def format_relative(value) -> str:
    """Format datetime as relative time."""
    if not value:
        return ""
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    
    now = datetime.now(timezone.utc)
    diff = now - value
    
    if diff.total_seconds() < 60:
        return "Just now"
    if diff.total_seconds() < 3600:
        mins = int(diff.total_seconds() / 60)
        return f"{mins}m ago"
    if diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    if diff.days < 7:
        return f"{diff.days}d ago"
    return value.strftime("%b %d")


# Register filters
templates.env.filters['nl2br'] = nl2br
templates.env.filters['format_date'] = format_date
templates.env.filters['format_datetime'] = format_datetime
templates.env.filters['format_relative'] = format_relative


def generate_csrf_token(request: Request) -> str:
    """Generate CSRF token for forms."""
    import secrets
    session_token = request.cookies.get("vault_session", "")
    random_part = secrets.token_hex(16)
    combined = f"{session_token}:{random_part}:{settings.SECRET_KEY}"
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def get_template_context(request: Request, **kwargs) -> dict:
    """Build common template context."""
    return {
        "request": request,
        "csrf_token": generate_csrf_token(request),
        "platform_fingerprint": getattr(settings, 'PLATFORM_PGP_FINGERPRINT', None),
        "onion_hostname": getattr(settings, 'ONION_HOSTNAME', None),
        "fee_percent": getattr(settings, 'DONATION_FEE_PERCENT', 5),
        "confirmations_required": getattr(settings, 'MONERO_CONFIRMATIONS_REQUIRED', 10),
        **kwargs
    }




@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Homepage."""
    return templates.TemplateResponse(
        "index.html", 
        get_template_context(request, current_user=current_user)
    )


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """Registration page."""
    return templates.TemplateResponse("register.html", get_template_context(request))


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", get_template_context(request))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """User dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        get_template_context(request, user=current_user)
    )


@router.get("/leads", response_class=HTMLResponse)
async def leads(request: Request):
    """Browse leads page."""
    return templates.TemplateResponse("leads.html", get_template_context(request))


@router.get("/listings", response_class=HTMLResponse)
async def listings(request: Request):
    """Browse support listings page."""
    return templates.TemplateResponse("listings.html", get_template_context(request))


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page."""
    return templates.TemplateResponse("about.html", get_template_context(request))


# Marketplace routes
@router.get("/marketplace", response_class=HTMLResponse)
async def marketplace(
    request: Request,
    category: Optional[str] = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Browse marketplace opportunities."""
    page_size = 20
    query = select(Lead).where(Lead.status == LeadStatus.PUBLISHED)
    
    if category:
        query = query.where(Lead.category == category)
    
    query = query.order_by(Lead.created_at.desc())
    
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    opportunities = result.scalars().all()
    
    return templates.TemplateResponse(
        "marketplace/browse.html",
        get_template_context(
            request,
            opportunities=opportunities,
            category_filter=category,
            page=page,
            total_pages=(total + page_size - 1) // page_size,
        )
    )


@router.get("/support", response_class=HTMLResponse)
async def support_listings(
    request: Request,
    category: Optional[str] = None,
    page: int = 1,
    db: AsyncSession = Depends(get_db),
):
    """Browse vendor support listings."""
    page_size = 20
    query = select(SupportListing).where(SupportListing.status == ListingStatus.ACTIVE)
    
    if category:
        query = query.where(SupportListing.category == category)
    
    query = query.order_by(SupportListing.created_at.desc())
    
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return templates.TemplateResponse(
        "support/browse.html",
        get_template_context(
            request,
            listings=listings,
            category_filter=category,
            page=page,
            total_pages=(total + page_size - 1) // page_size,
        )
    )

@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    """FAQ page."""
    return templates.TemplateResponse(
        "faq.html",
        get_template_context(request)
    )


@router.get("/security", response_class=HTMLResponse)
async def security_page(request: Request):
    """Security information page."""
    return templates.TemplateResponse(
        "security.html",
        get_template_context(request)
    )
