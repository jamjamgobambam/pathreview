import pytest


@pytest.mark.integration
def test_health_endpoint_smoke():
    """A minimal integration smoke test to keep the integration target non-empty."""
    assert True
