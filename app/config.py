"""Application configuration with environment variable support."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    
    # Application
    APP_NAME: str = Field(default="ARCHITECT // VAULT")
    APP_VERSION: str = Field(default="1.0.0")
    SECRET_KEY: str = Field(..., min_length=64)
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://vault:vault@localhost:5432/vault"
    )
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_MAX_OVERFLOW: int = Field(default=40)
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_SESSION_DB: int = Field(default=1)
    REDIS_RATELIMIT_DB: int = Field(default=2)
    
    # Session
    SESSION_LIFETIME_HOURS: int = Field(default=24)
    SESSION_SLIDING_WINDOW: bool = Field(default=True)
    SESSION_CIRCUIT_BINDING: bool = Field(default=True)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_USER: int = Field(default=100)  # per hour
    RATE_LIMIT_PER_CIRCUIT: int = Field(default=500)  # per hour
    RATE_LIMIT_AUTH_ATTEMPTS: int = Field(default=5)  # per 15 minutes
    
    # PGP
    GPG_HOME_DIR: str = Field(default="/var/lib/vault/gpg")
    GPG_BINARY: str = Field(default="/usr/bin/gpg")
    CHALLENGE_LENGTH: int = Field(default=32)
    CHALLENGE_TTL_SECONDS: int = Field(default=300)
    MAX_AUTH_ATTEMPTS: int = Field(default=5)
    LOCKOUT_DURATION_SECONDS: int = Field(default=900)
    
    # Monero
    MONERO_RPC_URL: str = Field(default="http://localhost:18081/json_rpc")
    MONERO_RPC_USER: Optional[str] = Field(default=None)
    MONERO_RPC_PASSWORD: Optional[str] = Field(default=None)
    MONERO_WALLET_RPC_URL: str = Field(default="http://localhost:18083/json_rpc")
    MONERO_WALLET_NAME: str = Field(default="vault_wallet")
    MONERO_WALLET_PASSWORD: str = Field(...)
    MONERO_CONFIRMATIONS_REQUIRED: int = Field(default=10)
    
    # Price Oracle
    PRICE_CACHE_TTL_SECONDS: int = Field(default=300)
    PRICE_API_URLS: list[str] = Field(
        default=[
            "https://api.coingecko.com/api/v3/simple/price?ids=monero&vs_currencies=usd",
            "https://api.kraken.com/0/public/Ticker?pair=XMRUSD",
        ]
    )
    
    # Subscriptions
    SUBSCRIPTION_FREELANCER_USD: int = Field(default=50)
    SUBSCRIPTION_OUTLET_USD: int = Field(default=500)
    SUBSCRIPTION_ENTERPRISE_USD: int = Field(default=2000)
    
    # Tor
    TOR_ENABLED: bool = Field(default=True)
    ONION_ADDRESS: Optional[str] = Field(default=None)
    
    # Storage
    UPLOAD_DIR: str = Field(default="/var/lib/vault/uploads")
    MAX_UPLOAD_SIZE_MB: int = Field(default=25)
    ALLOWED_EXTENSIONS: set[str] = Field(
        default={"txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "zip", "7z"}
    )
    
    # Security
    ALLOWED_ORIGINS: list[str] = Field(default=["https://*.onion"])
    TRUSTED_PROXY_IPS: list[str] = Field(default=["127.0.0.1", "::1"])
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/3")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/4")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: Optional[str] = Field(default="/var/log/vault/app.log")
    
    # Admin
    INITIAL_ADMIN_USERNAME: str = Field(default="admin")
    INITIAL_ADMIN_PGP_KEY: Optional[str] = Field(default=None)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
