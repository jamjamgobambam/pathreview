"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://pathreview:pathreview@localhost:5432/pathreview_dev"
    redis_url: str = "redis://localhost:6379/0"
    vector_db_url: str = "http://localhost:8001"
    llm_provider: str = "mock"
    openai_api_key: str = ""
    app_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"
    log_level: str = "INFO"
    github_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
