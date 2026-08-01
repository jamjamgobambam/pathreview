from core.config import Settings


def test_settings_redis_defaults() -> None:
    """Test that the Settings model correctly initializes Redis connection fields."""
    # Instantiate the settings model
    settings = Settings()

    # Verify the fields exist and have the expected default values
    assert hasattr(settings, "redis_host"), "Settings is missing redis_host"
    assert settings.redis_host == "localhost"

    assert hasattr(settings, "redis_port"), "Settings is missing redis_port"
    assert settings.redis_port == 6379
