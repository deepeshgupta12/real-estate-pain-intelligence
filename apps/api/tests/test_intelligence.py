from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_intelligence_processing_flow() -> None:
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

    evidence_response = client.post(
        "/api/v1/evidence",
        json={
            "scrape_run_id": run_id,
            "source_name": "reddit",
            "platform_name": "Square Yards",
            "content_type": "comment",
            "raw_text": "The listings shown were outdated and the agent never called back.",
            "cleaned_text": "The listings shown were outdated and the agent never called back.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    normalization_response = client.post(f"/api/v1/normalization/{run_id}")
    assert normalization_response.status_code == 200

    multilingual_response = client.post(f"/api/v1/multilingual/{run_id}")
    assert multilingual_response.status_code == 200

    intelligence_response = client.post(f"/api/v1/intelligence/{run_id}")
    assert intelligence_response.status_code == 200
    payload = intelligence_response.json()

    assert payload["run_id"] == run_id
    assert payload["total_evidence"] >= 1
    assert payload["insights_generated"] >= 1
    assert payload["pipeline_stage"] == "intelligence_completed"

    insights_response = client.get(f"/api/v1/intelligence/{run_id}")
    assert insights_response.status_code == 200
    insights_payload = insights_response.json()
    assert len(insights_payload) >= 1
    assert insights_payload[0]["pain_point_label"] is not None
    assert insights_payload[0]["taxonomy_cluster"] is not None
    assert insights_payload[0]["priority_label"] is not None
    assert insights_payload[0]["action_recommendation"] is not None