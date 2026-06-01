"""
Crisis Lens-specific signal processing orchestration.
Connects the reusable AI module to the database and event pipeline.
"""
import logging

from sqlalchemy.orm import Session

from app.ai import analysis_service
from app.ai.analysis_service import PROMPT_VERSION
from app.common.timestamps import utcnow
from app.events import service as event_service
from app.events.schemas import AnalysisResponse
from app.replay.models import ReplaySignal

logger = logging.getLogger(__name__)


def _signal_to_dict(signal: ReplaySignal) -> dict:
    return {
        "id": signal.id,
        "source_type": signal.source_type,
        "source_name": signal.source_name,
        "title": signal.title,
        "published_at": str(signal.published_at) if signal.published_at else None,
        "summary": signal.summary,
        "body": signal.body,
        "url": signal.url,
        "category_hint": signal.category_hint,
        "matched_keywords": signal.matched_keywords,
        "latitude": signal.latitude,
        "longitude": signal.longitude,
        "event_category": signal.event_category,
        "event_status": signal.event_status,
    }


def process_signal(db: Session, signal: ReplaySignal) -> AnalysisResponse:
    logger.info("Processing signal id=%d source=%s", signal.id, signal.source_type)

    try:
        result = analysis_service.analyze_signal(_signal_to_dict(signal))
    except Exception as exc:
        logger.exception("Gemini analysis failed for signal id=%d", signal.id)
        signal.status = "failed"
        signal.processing_error = str(exc)[:500]
        db.commit()
        raise

    ai_analysis = event_service.create_ai_analysis(db, signal, result, PROMPT_VERSION)

    if result.is_event_worthy:
        event = event_service.create_event(db, signal, ai_analysis, result)
        signal.status = "processed"
        signal.processed_at = utcnow()
        db.commit()
        logger.info("Signal id=%d accepted → event id=%d", signal.id, event.id)
        return AnalysisResponse(
            signal_id=signal.id,
            outcome="accepted",
            analysis_id=ai_analysis.id,
            is_event_worthy=True,
            event_type=result.event_type,
            severity=result.severity,
            confidence=result.confidence,
            title=result.title,
            event_id=event.id,
        )
    else:
        signal.status = "rejected"
        db.commit()
        logger.info("Signal id=%d rejected: %s", signal.id, result.rejection_reason)
        return AnalysisResponse(
            signal_id=signal.id,
            outcome="rejected",
            analysis_id=ai_analysis.id,
            is_event_worthy=False,
            event_type=result.event_type,
            severity=result.severity,
            confidence=result.confidence,
            rejection_reason=result.rejection_reason,
        )
