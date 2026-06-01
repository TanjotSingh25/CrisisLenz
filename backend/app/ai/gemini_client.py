import logging

from google import genai
from google.genai import types

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

        raw_text = response.text
        logger.debug("Gemini response: %d chars", len(raw_text))

        return SignalAnalysisResult.model_validate_json(raw_text)
