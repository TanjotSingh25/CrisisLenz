import logging

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.ai.schemas import SignalAnalysisResult
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def analyze_signal(self, system_prompt: str, user_prompt: str) -> SignalAnalysisResult:
        logger.info("Calling Gemini model: %s", settings.gemini_model)

        response = self._client.models.generate_content(
            model=settings.gemini_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            ),
        )

        raw_text = response.text or ""
        logger.info("Gemini raw response (%d chars): %s", len(raw_text), raw_text)

        try:
            return SignalAnalysisResult.model_validate_json(raw_text)
        except ValidationError as exc:
            # Surface exactly what Gemini returned so the failure is debuggable.
            logger.error(
                "Gemini response failed schema validation.\n--- RAW GEMINI RESPONSE ---\n%s\n--- VALIDATION ERROR ---\n%s",
                raw_text,
                exc,
            )
            raise
