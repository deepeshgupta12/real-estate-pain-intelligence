from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_human_review_flow() -> None:
    run_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "reddit",
            "target_brand": "99acres",
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
            "platform_name": "99acres",
            "content_type": "comment",
            "raw_text": "The listing looked outdated and the agent did not reply.",
            "cleaned_text": "The listing looked outdated and the agent did not reply.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200
    assert client.post(f"/api/v1/intelligence/{run_id}").status_code == 200

    generate_response = client.post(f"/api/v1/human-review/generate/{run_id}")
    assert generate_response.status_code == 200
    generate_payload = generate_response.json()
    assert generate_payload["run_id"] == run_id
    assert generate_payload["generated_count"] >= 1
    assert generate_payload["pipeline_stage"] == "human_review_queue_ready"

    queue_response = client.get(f"/api/v1/human-review?run_id={run_id}")
    assert queue_response.status_code == 200
    queue_payload = queue_response.json()
    assert len(queue_payload) >= 1
    review_item_id = queue_payload[0]["id"]
    assert queue_payload[0]["review_status"] == "pending_review"

    approve_response = client.post(
        f"/api/v1/human-review/approve/{review_item_id}",
        json={"reviewer_notes": "Looks valid"},
    )
    assert approve_response.status_code == 200
    approve_payload = approve_response.json()
    assert approve_payload["review_status"] == "reviewed"
    assert approve_payload["reviewer_decision"] == "approved"
    assert approve_payload["reviewer_notes"] == "Looks valid"