from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.health import router

# Create a lightweight FastAPI app to mount just the health router
app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_health_endpoint_resolves_without_crash() -> None:
    """Test that the health endpoint handles dependency checks without crashing."""
    response = client.get("/health")

    # We expect a 200 (healthy) or 503 (graceful unhealthy due to missing DBs).
    # If the AttributeError bug was present, this would return a 500.
    assert response.status_code in [200, 503]
