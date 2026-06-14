"""
Crisis Lens signal ingestion pipeline.

ingest_signal() is the single entry point for all signal processing.
It accepts a plain dict so any source can call it — the replay simulator,
a live API connector, a webhook receiver, or a direct API call.

The replay_signal parameter is optional. When provided (i.e. the signal
came through the simulator), it gets its status updated. When absent
(direct ingest or production path), no simulator record is touched.
"""
import logging

from sqlalchemy.orm import Session

from app.ai import analysis_service
from app.ai.analysis_service import PROMPT_VERSION
from app.ai.gemini_client import GeminiRateLimitError
from app.common.timestamps import utcnow
from app.events import service as event_service
from app.events.schemas import AnalysisResponse
from app.replay.models import ReplaySignal

logger = logging.getLogger(__name__)


def ingest_signal(
    db: Session,
    signal_data: dict,
    replay_signal: ReplaySignal | None = None,
) -> AnalysisResponse:
    """
    Core pipeline: analyze a signal with Gemini, store results, return outcome.

    signal_data   — plain dict, works from any source
    replay_signal — optional ORM object; if provided its status is updated
    """
    signal_id = signal_data.get("id") or (replay_signal.id if replay_signal else None)
    logger.info(
        "Ingesting signal id=%s source=%s title=%r",
        signal_id,
        signal_data.get("source_type"),
        (signal_data.get("title") or "")[:80],
    )

    try:
        result = analysis_service.analyze_signal(signal_data)
    except GeminiRateLimitError:
        # Transient quota exhaustion — do NOT mark the signal failed. Leave it
        # "released" so it can be retried once the per-minute window resets.
        logger.warning("Signal id=%s left released for retry — all models rate-limited.", signal_id)
        raise
    except Exception as exc:
        logger.exception("Gemini analysis failed for signal id=%s", signal_id)
        if replay_signal is not None:
            replay_signal.status = "failed"
            replay_signal.processing_error = str(exc)[:500]
            db.commit()
        raise

    replay_signal_id = replay_signal.id if replay_signal else None
    ai_analysis = event_service.create_ai_analysis(db, replay_signal_id, result, PROMPT_VERSION)

    if result.is_event_worthy:
        event = event_service.create_event(db, replay_signal_id, ai_analysis, result)
        if replay_signal is not None:
            replay_signal.status = "processed"
            replay_signal.processed_at = utcnow()
        db.commit()
        logger.info("Signal id=%s accepted → event id=%d", signal_id, event.id)
        return AnalysisResponse(
            signal_id=signal_id,
            outcome="accepted",
            analysis_id=ai_analysis.id,
            is_event_worthy=True,
            event_type=result.event_type,
            severity=result.severity,
            confidence=result.confidence,
            title=result.title,
            summary=result.summary,
            location_name=result.location_name,
            latitude=result.latitude,
            longitude=result.longitude,
            business_impact=result.business_impact,
            recommended_action=result.recommended_action,
            reasoning_brief=result.reasoning_brief,
            event_id=event.id,
        )
    else:
        if replay_signal is not None:
            replay_signal.status = "rejected"
        db.commit()
        logger.info("Signal id=%s rejected: %s", signal_id, result.rejection_reason)
        return AnalysisResponse(
            signal_id=signal_id,
            outcome="rejected",
            analysis_id=ai_analysis.id,
            is_event_worthy=False,
            event_type=result.event_type,
            severity=result.severity,
            confidence=result.confidence,
            reasoning_brief=result.reasoning_brief,
            rejection_reason=result.rejection_reason,
        )


def replay_signal_to_dict(signal: ReplaySignal) -> dict:
    """Convert a ReplaySignal ORM object to a plain dict for ingest_signal()."""
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
