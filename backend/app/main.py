import logging

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from app.ai.routes import router as ai_router
from app.alerts.routes import router as alerts_router
from app.clients.routes import router as clients_router
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

app = FastAPI(title="Crisis Lens", version="0.9.0")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Allow the local dev dashboard (Vite) to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Full traceback to the console (Docker logs) so errors persist and are
    # easy to capture. The response carries the real message too, so it shows
    # up in the dashboard toast instead of a generic "ValidationError".
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    # Starlette's error middleware sits OUTSIDE CORSMiddleware, so 500 responses
    # normally lack CORS headers — the browser then reports a misleading "CORS
    # policy" error instead of the real message. Add the headers back manually.
    origin = request.headers.get("origin")
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Vary"] = "Origin"
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {str(exc)[:800]}"},
        headers=headers,
    )


@app.on_event("startup")
def startup() -> None:
    run_migrations()
    configure_logging()  # re-assert after Alembic's fileConfig reset the root logger


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
