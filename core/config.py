"""Application configuration loaded from environment variables and .env file."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with support for .env file and environment variables."""

    # Database
    database_url: str = Field(default="postgresql+asyncpg://pathreview:pathreview@localhost:5432/pathreview_dev")
    redis_url: str = Field(default="redis://localhost:6379/0")
    vector_db_url: str = Field(default="http://localhost:8001")

    # LLM Configuration
    llm_provider: str = Field(default="mock")
    openai_api_key: str = Field(default="")
    openrouter_api_key: str = Field(default="")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_model: str = Field(default="google/gemma-3-27b-it:free")

    # Application
    app_env: str = Field(default="development")
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    log_level: str = Field(default="INFO")

    # GitHub
    github_token: str = Field(default="")

    # JWT
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)

    # Feature Limits
    max_repos_per_profile: int = Field(default=5)
    max_chunks_per_query: int = Field(default=10)
    min_relevance_score: float = Field(default=0.3)

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()
