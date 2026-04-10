from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_name"] == "Real Estate Pain Point Intelligence API"
    assert payload["environment"] == "development"
    assert payload["version"] == "0.2.0"
    assert payload["api_prefix"] == "/api/v1"