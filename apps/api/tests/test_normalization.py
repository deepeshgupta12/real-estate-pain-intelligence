from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_run_normalization_flow() -> None:
    run_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "reddit",
            "target_brand": "Housing.com",
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

    normalize_response = client.post(f"/api/v1/normalization/{run_id}")
    assert normalize_response.status_code == 200
    payload = normalize_response.json()

    assert payload["run_id"] == run_id
    assert payload["total_evidence"] >= 1
    assert payload["normalized_count"] >= 1
    assert payload["pipeline_stage"] == "normalization_completed"

    summary_response = client.get(f"/api/v1/normalization/{run_id}")
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert len(summary_payload) >= 1
    assert summary_payload[0]["normalization_status"] == "normalized"
    assert summary_payload[0]["normalization_hash"] is not None


def test_evidence_endpoint_returns_normalization_fields() -> None:
    response = client.get("/api/v1/evidence")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    if payload:
        assert "normalized_text" in payload[0]
        assert "normalized_language" in payload[0]
        assert "normalization_status" in payload[0]
        assert "normalization_hash" in payload[0]