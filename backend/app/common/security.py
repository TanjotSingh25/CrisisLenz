"""Lightweight security helpers for the demo: CORS-on-errors and an optional
admin token for mutation endpoints. This is deliberately minimal — Crisis Lens
is a demo, not a multi-tenant SaaS, so there is no user auth / RBAC here."""
from starlette.requests import Request

from app.config import settings

# Methods that change state. GET/HEAD/OPTIONS are always allowed.
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def cors_headers(request: Request) -> dict[str, str]:
    """
    Starlette's error middleware sits OUTSIDE CORSMiddleware, so error responses
    normally lack CORS headers — the browser then reports a misleading "CORS
    policy" error instead of the real message. Re-add them for allowed origins.
    """
    origin = request.headers.get("origin")
    if origin in settings.allowed_origins_list:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }
    return {}


def admin_token_ok(request: Request) -> bool:
    """
    True if the request is allowed past the admin-token guard.

    - No DEMO_ADMIN_TOKEN configured -> always allowed (local demo default).
    - Non-mutating method -> always allowed.
    - Otherwise the X-Demo-Admin-Token header must match exactly.
    """
    if not settings.demo_admin_token:
        return True
    if request.method.upper() not in MUTATING_METHODS:
        return True
    return request.headers.get("x-demo-admin-token", "") == settings.demo_admin_token
