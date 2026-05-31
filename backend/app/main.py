from fastapi import FastAPI

from app.database import Base, engine
from app.replay.routes import router as replay_router

app = FastAPI(title="Crisis Lens", version="0.1.0")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(replay_router)
