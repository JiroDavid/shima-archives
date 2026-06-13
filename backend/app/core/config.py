from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "ShimaVault API"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = ["http://localhost:3000"]

    # Postgres (async driver, e.g. postgresql+asyncpg://...)
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/shimavault"
    )

    # Twitch
    twitch_client_id: str = ""
    twitch_client_secret: str = ""
    twitch_redirect_uri: str = "https://localhost:8000/api/v1/auth/twitch/callback"

    # Embeddings / LLM
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Vector store
    chroma_path: str = "./chroma"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
