"""OWASP Security Headers ASGI middleware.

Injects the following response headers on every request:

┌─────────────────────────────────────┬──────────────────────────────────────────┐
│ Header                              │ Value / Purpose                          │
├─────────────────────────────────────┼──────────────────────────────────────────┤
│ Strict-Transport-Security           │ Force HTTPS for 1 year + subdomains      │
│ X-Content-Type-Options              │ nosniff — block MIME-type sniffing       │
│ X-Frame-Options                     │ DENY — prevent clickjacking              │
│ X-XSS-Protection                    │ 0 — disable legacy IE filter (per OWASP) │
│ Referrer-Policy                     │ strict-origin-when-cross-origin          │
│ Permissions-Policy                  │ Disable camera, mic, geolocation, etc.   │
│ Content-Security-Policy             │ Restrictive policy (configurable via env)│
│ Cache-Control                       │ no-store for API responses               │
│ X-Request-ID                        │ UUID per request for tracing             │
└─────────────────────────────────────┴──────────────────────────────────────────┘

Notes
-----
- HSTS is only injected on HTTPS requests (or always if ``force_hsts=True``),
  preventing header leaks over HTTP in development.
- The CSP value is read from ``Settings.security_csp`` and can be overridden
  via the ``SECURITY_CSP`` environment variable without code changes.
- ``X-Request-ID`` is propagated from the incoming request if already set
  (useful when a load balancer injects it upstream).

Usage
-----
    from travel.infrastructure.security.security_headers import SecurityHeadersMiddleware
    app.add_middleware(SecurityHeadersMiddleware)
"""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from travel.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects OWASP-recommended security headers into every response.

    Parameters
    ----------
    app:
        Inner ASGI application.
    force_hsts:
        If ``True``, injects HSTS even on plain-HTTP requests.
        Defaults to ``False`` (only injected on HTTPS or behind a TLS terminator
        that sets ``X-Forwarded-Proto: https``).
    """

    def __init__(self, app: ASGIApp, force_hsts: bool = False) -> None:
        super().__init__(app)
        cfg = get_settings()
        self._hsts_max_age = cfg.security_hsts_max_age
        self._csp = cfg.security_csp
        self._force_hsts = force_hsts

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Resolve or generate a request-scoped trace ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

        response = await call_next(request)

        # ── Determine if the request arrived over TLS ──────────────────────
        is_https = (
            request.url.scheme == "https"
            or request.headers.get("X-Forwarded-Proto", "").lower() == "https"
        )

        # ── Inject headers ─────────────────────────────────────────────────

        # HSTS — only meaningful over HTTPS
        if is_https or self._force_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self._hsts_max_age}; includeSubDomains; preload"
            )

        # MIME-type sniffing prevention
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Clickjacking prevention
        response.headers["X-Frame-Options"] = "DENY"

        # Disable legacy XSS filter (modern browsers ignore it; keeping it
        # enabled can introduce vulnerabilities — OWASP recommends '0')
        response.headers["X-XSS-Protection"] = "0"

        # Referrer leakage reduction
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy — disable browser APIs not needed by a REST API
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

        # Content-Security-Policy (value from settings / env var)
        response.headers["Content-Security-Policy"] = self._csp

        # API responses must never be cached by default
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-store"

        # Distributed tracing
        response.headers["X-Request-ID"] = request_id

        # Remove headers that leak server information
        for _leak_header in ("Server", "X-Powered-By"):
            try:
                del response.headers[_leak_header]
            except KeyError:
                pass

        return response
