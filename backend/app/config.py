from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    gemini_api_key: str = ""
    # Primary model tried first on every request.
    gemini_model: str = "gemini-2.5-flash"
    # Comma-separated fallbacks, tried in order only when the primary is
    # rate-limited (429). Each model has its own free-tier quota bucket.
    gemini_fallback_models: str = "gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite"

    # --- Deployment / security ---
    # "development" (default) or "production". Production hides error detail
    # from API responses and requires secrets to be present at startup.
    environment: str = "development"
    # Comma-separated origins allowed to call the API from a browser.
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    # If set, mutation endpoints (POST/PUT/PATCH/DELETE) require the matching
    # X-Demo-Admin-Token header. Empty (default) = open, for local demos.
    demo_admin_token: str = ""

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

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() == "production"


settings = Settings()
