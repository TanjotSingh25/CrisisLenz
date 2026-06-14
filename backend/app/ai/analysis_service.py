"""
Reusable signal analysis service.
Accepts a plain signal dict, returns a validated SignalAnalysisResult.
No database or ORM dependencies — portable to other projects.
"""
import logging

from app.ai.gemini_client import GeminiClient
from app.ai.prompt_loader import build_user_prompt, load_system_prompt
from app.ai.schemas import SignalAnalysisResult

logger = logging.getLogger(__name__)

PROMPT_VERSION = "signal_analysis_v1"


def analyze_signal(signal_data: dict) -> SignalAnalysisResult:
    system_prompt = load_system_prompt()
    user_prompt = build_user_prompt(signal_data)

    logger.info(
        "Analyzing signal id=%s source=%s title=%r",
        signal_data.get("id"),
        signal_data.get("source_type"),
        (signal_data.get("title") or "")[:80],
    )

    client = GeminiClient()
    result = client.analyze_signal(system_prompt, user_prompt)

    logger.info(
        "Analysis done: is_event_worthy=%s event_type=%s severity=%s confidence=%s",
        result.is_event_worthy,
        result.event_type,
        result.severity,
        f"{result.confidence:.2f}" if result.confidence is not None else "n/a",
    )
    return result
