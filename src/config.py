"""Configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Required for bot + LLM
    openai_api_key: str = ""
    telegram_bot_token: str = ""

    # Opik (observability)
    opik_api_key: str | None = None
    opik_url: str | None = None  # for self-hosted

    # Google Calendar (optional until calendar agent is used)
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_refresh_token: str | None = None
    google_access_token: str | None = None
    google_calendar_id: str = "primary"
    google_timezone: str = "UTC"

    # Deployment
    webhook_url: str | None = None  # https://your-domain.com/webhook
    port: int = 8080
    bot_mode: str = "polling"  # "polling" | "webhook"

    # LLM
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7

    def validate_required(self) -> None:
        """Raise if required keys for basic run are missing."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

    def validate_webhook(self) -> None:
        """Raise if webhook mode is selected but URL is missing."""
        if self.bot_mode == "webhook" and not self.webhook_url:
            raise ValueError("WEBHOOK_URL is required when BOT_MODE=webhook")


def get_settings() -> Settings:
    """Return validated settings. Call after env is loaded."""
    s = Settings()
    s.validate_required()
    if s.bot_mode == "webhook":
        s.validate_webhook()
    return s
