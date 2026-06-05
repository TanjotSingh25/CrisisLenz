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

logger = logging.getLogger(__name__)

app = FastAPI(title="Crisis Lens", version="0.9.0")

# Allow the local dev dashboard (Vite) to call the API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}"},
    )


@app.on_event("startup")
def startup() -> None:
    run_migrations()


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
