"""Reproduction test for issue #155.

api/routes/health.py builds its Redis health probe from settings.redis_host
and settings.redis_port, but Settings (core/config.py) only defines
redis_url. This test documents that mismatch failing today.
"""

import pytest

from core.config import Settings


@pytest.mark.unit
def test_settings_has_no_redis_host_reproduces_issue_155():
    settings = Settings()

    with pytest.raises(AttributeError):
        _ = settings.redis_host
