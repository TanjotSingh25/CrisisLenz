from fastapi import FastAPI

from app.database import Base, engine
from app.providers.eonet.routes import router as eonet_router
from app.replay.routes import router as replay_router

app = FastAPI(title="Crisis Lens", version="0.2.0")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(replay_router)
app.include_router(eonet_router)
