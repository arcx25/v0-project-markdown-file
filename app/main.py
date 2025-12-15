"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.config import get_settings
from app.database import init_db
from app.dependencies import get_redis
from app.api.router import api_router
from app.web.routes import router as web_router
from app.web.admin_routes import router as admin_router
from app.web.dashboard_routes import router as dashboard_router
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware, TorCircuitMiddleware
from app.web.error_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException


settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    await init_db()
    logger.info("Database initialized")
    
    # Initialize Redis
    redis = await get_redis()
    logger.info("Redis connected")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await redis.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None,
    openapi_url=None if settings.is_production else "/openapi.json",
    lifespan=lifespan
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TorCircuitMiddleware)

# Add rate limiting middleware with Redis
@app.on_event("startup")
async def add_rate_limiting():
    redis = await get_redis()
    app.add_middleware(RateLimitMiddleware, redis=redis)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(api_router)
app.include_router(web_router)
app.include_router(dashboard_router)
app.include_router(admin_router)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
