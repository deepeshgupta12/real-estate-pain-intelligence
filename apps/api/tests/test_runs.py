from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_list_scrape_runs() -> None:
    create_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "reddit",
            "target_brand": "Square Yards",
            "status": "created",
            "items_discovered": 12,
            "items_processed": 0,
        },
    )
    assert create_response.status_code == 201
    created_payload = create_response.json()
    assert created_payload["source_name"] == "reddit"
    assert created_payload["target_brand"] == "Square Yards"

    list_response = client.get("/api/v1/runs")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1