import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, SessionLocal, engine
from app.providers.eonet.routes import router as eonet_router
from app.replay import service as replay_service
from app.replay.routes import router as replay_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Crisis Lens", version="0.3.0")


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}"},
    )


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
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
