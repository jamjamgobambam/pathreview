"""Reproduction for issue #70: no per-IP rate limiting exists.

`safety.rate_limiter.RateLimiter` is a working, tested class, but nothing in
`api/main.py` or `api/middleware/` ever instantiates it or calls
`check_rate_limit`. As a result, unauthenticated requests to public
endpoints are never throttled, regardless of volume or source IP.

This test currently FAILS: it sends far more requests than
`settings.rate_limit_per_minute` allows and expects at least one 429, but
today every single request succeeds.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.config import settings


@pytest.mark.integration
def test_unauthenticated_requests_are_never_rate_limited() -> None:
    request_count = settings.rate_limit_per_minute + 20

    with TestClient(app) as client:
        status_codes = [client.get("/").status_code for _ in range(request_count)]

    assert 429 in status_codes, (
        f"Sent {request_count} unauthenticated requests (limit is "
        f"{settings.rate_limit_per_minute}/min) and got zero 429s back — "
        "no per-IP rate limiting is applied to public endpoints."
    )
