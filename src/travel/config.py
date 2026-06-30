"""Application settings loaded from environment variables via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object. All fields are strongly typed."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # -------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------
    database_url: PostgresDsn = Field(
        default=...,  # type: ignore[assignment]
        description=(
            "Async PostgreSQL DSN. "
            "Example: postgresql+asyncpg://user:pass@localhost:5432/dbname"
        ),
    )
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=200)
    db_pool_timeout: int = Field(default=30, ge=1)
    db_echo: bool = Field(default=False)

    # -------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    secret_key: str = Field(default="change-me-in-production", min_length=16)
    api_v1_prefix: str = Field(default="/api/v1")

    # -------------------------------------------------------------------
    # Celery / Redis
    # -------------------------------------------------------------------
    celery_broker_url: str = Field(default="redis://localhost:6379/0")
    celery_result_backend: str = Field(default="redis://localhost:6379/1")
    redis_url: str = Field(default="redis://localhost:6379/0")

    # -------------------------------------------------------------------
    # Proxy rotation
    # -------------------------------------------------------------------
    proxy_list: str = Field(
        default="",
        description="Comma-separated list of proxy URLs (socks5/http)",
    )

    @property
    def proxy_urls(self) -> list[str]:
        """Return the proxy list as a parsed Python list."""
        if not self.proxy_list:
            return []
        return [p.strip() for p in self.proxy_list.split(",") if p.strip()]

    # -------------------------------------------------------------------
    # Circuit Breaker
    # -------------------------------------------------------------------
    circuit_breaker_threshold: int = Field(
        default=3,
        ge=1,
        description="Number of consecutive 429s before opening the circuit",
    )
    circuit_breaker_timeout_seconds: int = Field(
        default=900,
        ge=60,
        description="How long (seconds) to pause a tripped domain (default: 15 min)",
    )

    # -------------------------------------------------------------------
    # Scraper concurrency
    # -------------------------------------------------------------------
    scraper_max_concurrent_pages: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Max simultaneous Playwright pages per worker process",
    )

    # -------------------------------------------------------------------
    # Security — CORS
    # -------------------------------------------------------------------
    allowed_origins: str = Field(
        default="",
        description=(
            "Comma-separated list of allowed CORS origins. "
            "Example: https://app.example.com,https://admin.example.com. "
            "Wildcards (*) are NEVER permitted."
        ),
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return parsed, validated CORS origin list — never contains '*'."""
        if not self.allowed_origins:
            return []
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        # Hard guard: reject any wildcard that slips through
        return [o for o in origins if o != "*"]

    # -------------------------------------------------------------------
    # Security — Rate Limiting
    # -------------------------------------------------------------------
    rate_limit_global_requests: int = Field(
        default=50,
        ge=1,
        description="Max requests per IP per minute (global endpoints)",
    )
    rate_limit_search_requests: int = Field(
        default=5,
        ge=1,
        description="Max requests per IP per second (search/aggregation endpoints)",
    )
    rate_limit_enabled: bool = Field(
        default=True,
        description="Master switch — set to False in integration tests",
    )

    # -------------------------------------------------------------------
    # Security — OWASP headers
    # -------------------------------------------------------------------
    security_hsts_max_age: int = Field(
        default=31536000,  # 1 year in seconds
        description="Strict-Transport-Security max-age in seconds",
    )
    security_csp: str = Field(
        default=(
            "default-src 'none'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        description="Content-Security-Policy header value",
    )

    @model_validator(mode="after")
    def validate_database_scheme(self) -> "Settings":
        scheme = self.database_url.scheme
        if "asyncpg" not in scheme:
            raise ValueError(
                f"database_url must use asyncpg driver, got scheme: '{scheme}'"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings factory — call this everywhere instead of Settings()."""
    return Settings()
