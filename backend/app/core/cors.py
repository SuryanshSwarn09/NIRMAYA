"""CORS resolution and enterprise security headers configuration."""

from typing import List, Dict
from app.core.config import settings


def get_allowed_origins() -> List[str]:
    """Retrieve normalized list of permitted CORS origins.

    Includes configured origins and ensures no trailing slashes.
    """
    origins = set()
    for origin in settings.BACKEND_CORS_ORIGINS:
        cleaned = origin.strip().rstrip("/")
        if cleaned:
            origins.add(cleaned)
    return sorted(list(origins))


def get_security_headers() -> Dict[str, str]:
    """Provide standard security headers for healthcare information compliance."""
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
        "X-Permitted-Cross-Domain-Policies": "none",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        ),
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-site",
    }
    if settings.is_production or settings.SECURITY_HSTS_SECONDS > 0:
        headers["Strict-Transport-Security"] = (
            f"max-age={settings.SECURITY_HSTS_SECONDS}; includeSubDomains; preload"
        )
    return headers
