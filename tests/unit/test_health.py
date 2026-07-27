"""Tests reproducing issue #155: health check references settings.redis_host,
which does not exist on Settings.
"""

import pytest

from core.config import Settings


@pytest.mark.unit
class TestHealthRedisConfig:
    """Reproduction tests for the Settings/health.py field mismatch."""

    def test_settings_has_no_redis_host_field(self) -> None:
        """Settings only exposes redis_url; redis_host does not exist.

        api/routes/health.py builds its Redis client from settings.redis_host
        and settings.redis_port (lines 45-46), but Settings (core/config.py)
        only defines redis_url. This asserts the field is currently absent,
        confirming the root cause of issue #155.
        """
        settings = Settings()

        assert hasattr(settings, "redis_url")
        assert not hasattr(settings, "redis_host")
        assert not hasattr(settings, "redis_port")

    def test_health_redis_probe_raises_attribute_error(self) -> None:
        """Reproduces the exact failure inside health_check()'s Redis probe.

        This mirrors api/routes/health.py lines 39-56: it accesses
        settings.redis_host/redis_port before constructing the Redis client.
        In the real endpoint this AttributeError is swallowed by a bare
        except, so the caller never sees it directly -- instead Redis is
        always reported "unhealthy" (and the endpoint returns 503) even
        when Redis is actually reachable, since redis_url is never used.
        """
        settings = Settings()

        with pytest.raises(AttributeError, match="redis_host"):
            # getattr (not attribute access) so mypy doesn't flag the
            # missing field statically -- runtime AttributeError is the point.
            _ = getattr(settings, "redis_host")  # noqa: B009
