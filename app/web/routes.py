"""Web frontend routes."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Homepage."""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    """Registration page."""
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: User = Depends(get_current_user)):
    """User dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": current_user}
    )


@router.get("/leads", response_class=HTMLResponse)
async def leads(request: Request):
    """Browse leads page."""
    return templates.TemplateResponse("leads.html", {"request": request})


@router.get("/listings", response_class=HTMLResponse)
async def listings(request: Request):
    """Browse support listings page."""
    return templates.TemplateResponse("listings.html", {"request": request})


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About page."""
    return templates.TemplateResponse("about.html", {"request": request})
