"""Main API router."""

from fastapi import APIRouter
from app.api import auth, leads, messages, listings, admin, subscriptions

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(messages.router)
api_router.include_router(listings.router)
api_router.include_router(subscriptions.router)
api_router.include_router(admin.router)
