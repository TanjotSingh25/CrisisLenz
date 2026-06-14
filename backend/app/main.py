import logging

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from app.ai.gemini_client import GeminiRateLimitError
from app.ai.routes import router as ai_router
from app.alerts.routes import router as alerts_router
from app.clients.routes import router as clients_router
from app.common.security import admin_token_ok, cors_headers
from app.config import settings
from app.database import engine
from app.events.routes import router as events_router
from app.impact.routes import router as impact_router
from app.providers.eonet.routes import router as eonet_router
from app.replay.routes import router as replay_router
from app.signals.routes import router as signals_router

def configure_logging() -> None:
    """
    Send our app logs to the console at INFO. Called at import AND again after
    migrations, because Alembic's fileConfig resets the root logger to WARN
    (from alembic.ini) and would otherwise silence our INFO logs.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    logging.getLogger("app").setLevel(logging.INFO)


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Crisis Lens", version="1.0.0")

# Allow only the configured dashboard origins (no wildcard).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_admin_middleware(request: Request, call_next):
    # Optional admin-token guard for mutation endpoints (no-op unless
    # DEMO_ADMIN_TOKEN is set). OPTIONS/GET are never blocked.
    if not admin_token_ok(request):
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid X-Demo-Admin-Token."},
            headers=cors_headers(request),
        )
    response = await call_next(request)
    # Basic security headers.
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


def run_migrations() -> None:
    cfg = Config("alembic.ini")
    insp = inspect(engine)
    tables = insp.get_table_names()

    # Bootstrap: table exists from pre-Alembic era — stamp at 0001 so only
    # remaining migrations run (no data loss, no down -v needed).
    if "replay_signals" in tables and "alembic_version" not in tables:
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE alembic_version "
                "(version_num VARCHAR(32) NOT NULL, "
                "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
            ))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0001')"))
        logger.info("Bootstrapped Alembic version tracking — stamped at 0001.")

    command.upgrade(cfg, "head")


@app.exception_handler(GeminiRateLimitError)
async def rate_limit_handler(request: Request, exc: GeminiRateLimitError) -> JSONResponse:
    """All fallback models exhausted → 503 with a clear, actionable message."""
    logger.warning("Gemini rate limit (all models) on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
        headers=cors_headers(request),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Always log the full traceback to the console (Docker logs).
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    # In production, never leak internals (exception type, message, paths) to the
    # client. In development, return the real message to ease debugging.
    if settings.is_production:
        detail = "Internal server error. Check the backend logs."
    else:
        detail = f"{type(exc).__name__}: {str(exc)[:800]}"
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
        headers=cors_headers(request),
    )


def validate_required_secrets() -> None:
    """In production, refuse to start with missing secrets. In development, warn."""
    missing = [
        name
        for name, value in (("GEMINI_API_KEY", settings.gemini_api_key), ("DATABASE_URL", settings.database_url))
        if not value
    ]
    if not missing:
        return
    if settings.is_production:
        raise RuntimeError(f"Missing required secrets in production: {', '.join(missing)}")
    logger.warning("Missing secrets (ok for local dev): %s", ", ".join(missing))


@app.on_event("startup")
def startup() -> None:
    run_migrations()
    configure_logging()  # re-assert after Alembic's fileConfig reset the root logger
    validate_required_secrets()
    logger.info(
        "Crisis Lens started: environment=%s, admin_token=%s, origins=%s",
        settings.environment,
        "set" if settings.demo_admin_token else "disabled",
        settings.allowed_origins_list,
    )


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(signals_router)
app.include_router(replay_router)
app.include_router(eonet_router)
app.include_router(ai_router)
app.include_router(events_router)
app.include_router(clients_router)
app.include_router(impact_router)
app.include_router(alerts_router)
