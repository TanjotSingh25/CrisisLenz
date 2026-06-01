import logging

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text

from app.database import SessionLocal, engine
from app.providers.eonet.routes import router as eonet_router
from app.replay import service as replay_service
from app.replay.routes import router as replay_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Crisis Lens", version="0.3.0")


def run_migrations() -> None:
    cfg = Config("alembic.ini")
    insp = inspect(engine)
    tables = insp.get_table_names()

    # Bootstrap: table exists from pre-Alembic era (create_all), stamp it at 0001
    # so Alembic can take over from there and apply only the remaining migrations.
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
    db = SessionLocal()
    try:
        seeded = replay_service.seed_wikinews_if_empty(db)
        if seeded:
            logger.info("Seeded %d Wikinews signals into replay_signals.", seeded)
        else:
            logger.info("Wikinews signals already present — skipping seed.")
    finally:
        db.close()


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(replay_router)
app.include_router(eonet_router)
