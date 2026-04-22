from pathlib import Path

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    IS_PROD: bool = False

    # Database configuration
    DATABASE_USERNAME: str = "db_master_admin"
    DATABASE_PASSWORD: str = "db_master_admin_password"  # noqa: S105
    DATABASE_HOSTNAME: str = "0.0.0.0"  # noqa: S104
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "app_db"
    DATABASE_SCHEMA: str = "sample_schema"

    # Logging configuration
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_LEVEL: str = "INFO"

    # LLM / Agent configuration (OpenRouter via OpenAI-compatible API)
    OPENROUTER_API_KEY: SecretStr = SecretStr("")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_DEFAULT_MODEL: str = "openai/gpt-4o-mini"
    LLM_REQUEST_TIMEOUT_S: float = 60.0
    LLM_HTTP_REFERER: str | None = None
    LLM_APP_TITLE: str | None = None

    # Maximum number of persisted message rows fed back to the LLM as context per turn.
    # Older rows remain in the database for display but are omitted from the prompt window
    # so token usage stays bounded as conversations grow.  Set to 0 to disable clipping.
    AGENT_MAX_HISTORY_MESSAGES: int = 50

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        return (
            f"postgresql+psycopg://{self.DATABASE_USERNAME}:"
            f"{self.DATABASE_PASSWORD}@{self.DATABASE_HOSTNAME}:"
            f"{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


config = Config()
