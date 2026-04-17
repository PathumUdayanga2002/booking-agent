from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8001
    FASTAPI_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    JWT_SECRET_KEY: str = "replace-with-shared-secret"
    JWT_ALGORITHM: str = "HS256"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    EXPRESS_HOST: str = "localhost"
    EXPRESS_PORT: int = 5000
    EXPRESS_BACKEND_URL: str = "http://localhost:5000"
    HTTP_TIMEOUT_SECONDS: float = 10.0

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
