from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.replay import service
from app.replay.schemas import (
    LoadRequest,
    LoadResponse,
    MessageResponse,
    ReplaySignalOut,
    StatusResponse,
)

router = APIRouter(prefix="/replay", tags=["replay"])


@router.post("/load", response_model=LoadResponse)
def load_replay(body: LoadRequest = LoadRequest(), db: Session = Depends(get_db)):
    count = service.load_signals(db, reset_existing=body.reset_existing)
    return LoadResponse(loaded=count)


@router.get("/status", response_model=StatusResponse)
def replay_status(db: Session = Depends(get_db)):
    return service.get_status(db)


@router.post("/next", response_model=ReplaySignalOut)
def release_next(db: Session = Depends(get_db)):
    return service.release_next(db)


@router.get("/signals/released", response_model=list[ReplaySignalOut])
def list_released(db: Session = Depends(get_db)):
    return service.get_signals_by_status(db, "released")


@router.get("/signals/pending", response_model=list[ReplaySignalOut])
def list_pending(db: Session = Depends(get_db)):
    return service.get_signals_by_status(db, "pending")


@router.post("/reset", response_model=MessageResponse)
def reset_replay(db: Session = Depends(get_db)):
    count = service.reset_all(db)
    return MessageResponse(message=f"Reset {count} signals to pending.")


@router.delete("/clear", response_model=MessageResponse)
def clear_replay(db: Session = Depends(get_db)):
    count = service.clear_all(db)
    return MessageResponse(message=f"Cleared {count} signals from the table.")
