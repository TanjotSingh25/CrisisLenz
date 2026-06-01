import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.events.schemas import AnalysisResponse
from app.replay.models import ReplaySignal
from app.signals import processing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

_ALREADY_ANALYZED = {"processed", "rejected", "failed"}


def _get_released_signal(db: Session, signal_id: int) -> ReplaySignal:
    signal = db.query(ReplaySignal).filter(ReplaySignal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found.")
    if signal.status == "pending":
        raise HTTPException(status_code=422, detail="Signal has not been released yet. Call POST /replay/next first.")
    if signal.status in _ALREADY_ANALYZED:
        raise HTTPException(
            status_code=409,
            detail=f"Signal {signal_id} is already {signal.status}. Use POST /replay/reset to start over.",
        )
    return signal


@router.post("/analyze-signal/{signal_id}", response_model=AnalysisResponse)
def analyze_signal(signal_id: int, db: Session = Depends(get_db)):
    """Analyze a specific released signal by ID."""
    signal = _get_released_signal(db, signal_id)
    return processing.process_signal(db, signal)


@router.post("/analyze-next-released", response_model=AnalysisResponse)
def analyze_next_released(db: Session = Depends(get_db)):
    """Find the next released signal and analyze it."""
    signal = (
        db.query(ReplaySignal)
        .filter(ReplaySignal.status == "released")
        .order_by(ReplaySignal.release_order)
        .first()
    )
    if not signal:
        raise HTTPException(
            status_code=404,
            detail="No released signals waiting. Call POST /replay/next to release one.",
        )
    return processing.process_signal(db, signal)
