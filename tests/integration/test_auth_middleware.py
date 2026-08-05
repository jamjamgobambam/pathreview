"""Integration tests for authentication failures on protected routes."""

from datetime import timedelta

from fastapi.testclient import TestClient
from jose import jwt  # type: ignore[import-untyped]

from api.main import app
from core.config import settings
from core.security import create_access_token

client = TestClient(app)


def test_missing_authorization_header_returns_401() -> None:
    response = client.get("/reviews")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_malformed_token_returns_401() -> None:
    response = client.get(
        "/reviews",
        headers={"Authorization": "Bearer not_a_jwt_token"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


def test_expired_token_returns_401() -> None:
    token = create_access_token(
        {"sub": "test-user-id"},
        expires_delta=timedelta(minutes=-1),
    )

    response = client.get(
        "/reviews",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}


def test_token_signed_with_wrong_secret_returns_401() -> None:
    token = jwt.encode(
        {"sub": "test-user-id"},
        "different-secret",
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/reviews",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}
