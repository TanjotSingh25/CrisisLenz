import logging

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.ai.schemas import SignalAnalysisResult
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiRateLimitError(RuntimeError):
    """Raised when every model in the fallback chain is rate-limited (429)."""


class GeminiClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def analyze_signal(self, system_prompt: str, user_prompt: str) -> SignalAnalysisResult:
        """
        Try each model in settings.model_chain in order. The primary model is
        tried first on every call; if it is rate-limited (429), fall through to
        the next model (which has its own quota bucket). Non-rate-limit errors
        are raised immediately — fallback only helps with quota exhaustion.
        """
        chain = settings.model_chain
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        )

        last_rate_limit: Exception | None = None
        for index, model in enumerate(chain):
            logger.info("Calling Gemini model: %s (option %d/%d)", model, index + 1, len(chain))
            try:
                response = self._client.models.generate_content(
                    model=model, contents=user_prompt, config=config
                )
            except errors.ClientError as exc:
                if getattr(exc, "code", None) == 429:
                    last_rate_limit = exc
                    logger.warning(
                        "Model %s rate-limited (429). %s",
                        model,
                        "Trying next model." if index + 1 < len(chain) else "No models left.",
                    )
                    continue
                # Not a quota problem (bad request, auth, etc.) — fallback won't help.
                raise

            raw_text = response.text or ""
            # Log only a bounded preview — never dump unbounded model output.
            logger.info("Gemini response from %s: %d chars", model, len(raw_text))
            try:
                return SignalAnalysisResult.model_validate_json(raw_text)
            except ValidationError as exc:
                # Bad shape is not a quota problem — surface it, don't burn other
                # models. Log a capped preview of the raw response to debug it.
                logger.error(
                    "Gemini (%s) response failed schema validation.\n"
                    "--- RAW (first 1500 chars) ---\n%s\n--- VALIDATION ERROR ---\n%s",
                    model,
                    raw_text[:1500],
                    exc,
                )
                raise

        # Every model in the chain was rate-limited.
        logger.error("All %d Gemini models are rate-limited.", len(chain))
        raise GeminiRateLimitError(
            f"All configured Gemini models are rate-limited (tried: {', '.join(chain)}). "
            f"Free-tier quota exhausted — wait for the per-minute window to reset, or add more "
            f"fallback models via GEMINI_FALLBACK_MODELS."
        ) from last_rate_limit
