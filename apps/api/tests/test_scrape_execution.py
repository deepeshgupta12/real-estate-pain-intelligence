from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_supported_scraper_sources_list() -> None:
    response = client.get("/api/v1/scrape-execution/sources")
    assert response.status_code == 200

    payload = response.json()
    assert "reddit" in payload
    assert "youtube" in payload
    assert "app_reviews" in payload
    assert "x" in payload
    assert "review_sites" in payload


def test_execute_scrape_run_persists_evidence() -> None:
    run_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "reddit",
            "target_brand": "Square Yards",
            "status": "created",
            "pipeline_stage": "created",
            "trigger_mode": "manual",
            "items_discovered": 0,
            "items_processed": 0,
        },
    )
    assert run_response.status_code == 201
    run_id = run_response.json()["id"]

    execute_response = client.post(f"/api/v1/scrape-execution/{run_id}")
    assert execute_response.status_code == 200

    execute_payload = execute_response.json()
    assert execute_payload["run_id"] == run_id
    assert execute_payload["status"] == "completed"
    assert execute_payload["pipeline_stage"] == "completed"
    assert execute_payload["persisted_evidence_count"] >= 1

    evidence_response = client.get("/api/v1/evidence")
    assert evidence_response.status_code == 200
    evidence_items = evidence_response.json()
    assert len(evidence_items) >= 1