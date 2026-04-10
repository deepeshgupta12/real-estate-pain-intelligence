from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_system_info_endpoint() -> None:
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200

    payload = response.json()
    assert payload["app_name"] == "Real Estate Pain Point Intelligence API"
    assert payload["version"] == "0.2.0"
    assert payload["environment"] == "development"
    assert payload["database_configured"] is True