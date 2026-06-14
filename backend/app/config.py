from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str = ""
    # Primary model tried first on every request.
    gemini_model: str = "gemini-2.5-flash"
    # Comma-separated fallbacks, tried in order only when the primary is
    # rate-limited (429). Each model has its own free-tier quota bucket.
    gemini_fallback_models: str = "gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite"

    model_config = {"env_file": ".env"}

    @property
    def model_chain(self) -> list[str]:
        """Ordered list of models to try: primary first, then fallbacks. De-duplicated."""
        chain = [self.gemini_model.strip()]
        for m in self.gemini_fallback_models.split(","):
            name = m.strip()
            if name and name not in chain:
                chain.append(name)
        return chain


settings = Settings()
