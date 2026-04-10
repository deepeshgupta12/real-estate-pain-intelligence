from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_meta_endpoint() -> None:
    response = client.get("/api/v1/meta")
    assert response.status_code == 200

    payload = response.json()
    assert payload["app_name"] == "Real Estate Pain Point Intelligence API"
    assert payload["version"] == "0.2.0"
    assert payload["environment"] == "development"
    assert payload["api_prefix"] == "/api/v1"
    assert payload["frontend_url"] == "http://localhost:3000"
    assert payload["docs_url"] == "/docs"
    assert payload["openapi_url"] == "/openapi.json"