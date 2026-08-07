"""Integration tests for rate limit headers on responses.
Requires the app running locally (make run), Docker services up
(docker compose up -d), and the database seeded (make seed) so the
user1/user2/user3 accounts from scripts/seed_db.py exist.
"""

import base64
import json
import time
from collections.abc import Iterator

import httpx
import pytest
import redis

from core.config import settings
from core.security import create_access_token

BASE_URL = "http://localhost:8000"

pytestmark = pytest.mark.integration


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL)


@pytest.fixture
def redis_client() -> Iterator[redis.Redis]:
    client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    yield client
    client.close()


def login(client: httpx.Client, email: str, password: str) -> str:
    """Log in a seeded user via the real /auth/login endpoint and return the access token."""
    response = client.post("/auth/login", data={"username": email, "password": password})
    response.raise_for_status()
    return str(response.json()["access_token"])


def user_id_from_token(token: str) -> str:
    """Read the sub claim off a JWT without verifying it (token came from our own server)."""
    payload_b64 = token.split(".")[1]
    padding = "=" * (-len(payload_b64) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
    return str(payload["sub"])


def bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class TestRateLimitHeaders:
    def test_response_includes_rate_limit_headers(self, client: httpx.Client) -> None:
        response = client.get("/")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_remaining_decrements_across_requests(
        self, client: httpx.Client, redis_client: redis.Redis
    ) -> None:
        token = login(client, "user1@example.com", "password1")
        user_id = user_id_from_token(token)
        redis_client.delete(f"rate_limit:{user_id}")

        first = client.get("/", headers=bearer_headers(token))
        second = client.get("/", headers=bearer_headers(token))

        first_remaining = int(first.headers["X-RateLimit-Remaining"])
        second_remaining = int(second.headers["X-RateLimit-Remaining"])
        assert second_remaining == first_remaining - 1

    def test_limit_header_matches_configured_limit(self, client: httpx.Client) -> None:
        response = client.get("/")

        assert response.headers["X-RateLimit-Limit"] == str(settings.rate_limit_per_minute)

    def test_exceeding_limit_returns_429_with_zero_remaining(
        self, client: httpx.Client, redis_client: redis.Redis
    ) -> None:
        token = login(client, "user2@example.com", "password2")
        user_id = user_id_from_token(token)
        key = f"rate_limit:{user_id}"
        limit = settings.rate_limit_per_minute
        redis_client.delete(key)

        # Seed the bucket to one request away from the limit so we don't need
        # to fire `limit` real requests to reach it. Window-reset/recovery is
        # already covered by test_rate_limiter.py's mocked-time unit tests.
        now = time.time()
        redis_client.zadd(key, {f"seed-{i}": now for i in range(limit - 1)})
        redis_client.expire(key, 61)

        last_allowed = client.get("/", headers=bearer_headers(token))
        over_limit = client.get("/", headers=bearer_headers(token))

        assert last_allowed.status_code == 200
        assert last_allowed.headers["X-RateLimit-Remaining"] == "0"
        assert over_limit.status_code == 429
        assert over_limit.headers["X-RateLimit-Remaining"] == "0"

        redis_client.delete(key)

    def test_invalid_bearer_token_returns_200_with_headers(self, client: httpx.Client) -> None:
        response = client.get("/", headers=bearer_headers("not.a.valid.token"))

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_token_without_sub_returns_200_with_headers(self, client: httpx.Client) -> None:
        token = create_access_token(data={})

        response = client.get("/", headers=bearer_headers(token))

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_different_users_have_independent_remaining_counts(
        self, client: httpx.Client, redis_client: redis.Redis
    ) -> None:
        token1 = login(client, "user1@example.com", "password1")
        token3 = login(client, "user3@example.com", "password3")
        user_id1 = user_id_from_token(token1)
        user_id3 = user_id_from_token(token3)
        redis_client.delete(f"rate_limit:{user_id1}")
        redis_client.delete(f"rate_limit:{user_id3}")

        client.get("/", headers=bearer_headers(token1))
        client.get("/", headers=bearer_headers(token1))
        response_user1 = client.get("/", headers=bearer_headers(token1))
        response_user3 = client.get("/", headers=bearer_headers(token3))

        remaining_user1 = int(response_user1.headers["X-RateLimit-Remaining"])
        remaining_user3 = int(response_user3.headers["X-RateLimit-Remaining"])

        # user3's first request should not reflect user1's 3 prior requests.
        assert remaining_user3 == settings.rate_limit_per_minute - 1
        assert remaining_user1 < remaining_user3

    def test_no_auth_header_uses_ip_fallback(self, client: httpx.Client) -> None:
        response = client.get("/")

        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        remaining = int(response.headers["X-RateLimit-Remaining"])
        assert remaining >= 0
