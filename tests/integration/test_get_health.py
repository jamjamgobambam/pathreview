from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200


# from root, run the following command, pytest tests/integration/test_health.py::test_health.
# The test will fail the assumption since assert 503 != 200
