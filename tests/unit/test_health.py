import redis
from fastapi.testclient import TestClient

from api.main import app
from safety.monitoring import SafetyMonitor

client = TestClient(app)


def test_health_endpoint_returns_safety_events() -> None:
    # 1. Connect to local Redis and create SafetyMonitor instance
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    monitor = SafetyMonitor(r)

    # 2. Log dummy safety events
    monitor.log_event("pii_detected", {"field": "email"})
    monitor.log_event("injection_attempt", {"payload": "DROP TABLE"})
    monitor.log_event("pii_detected", {"field": "phone"})

    # 3. Call the health check endpoint
    response = client.get("/health")

    # 4. Assertions
    assert response.status_code == 200
    data = response.json()

    assert "safety_events_last_hour" in data
    assert data["safety_events_last_hour"] >= 3
