from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_notion_sync_flow() -> None:
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
            "raw_text": "The listing looked outdated and the agent did not respond.",
            "cleaned_text": "The listing looked outdated and the agent did not respond.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200
    assert client.post(f"/api/v1/intelligence/{run_id}").status_code == 200
    assert client.post(f"/api/v1/human-review/generate/{run_id}").status_code == 200

    queue_response = client.get(f"/api/v1/human-review?run_id={run_id}")
    assert queue_response.status_code == 200
    queue_payload = queue_response.json()
    assert len(queue_payload) >= 1
    review_item_id = queue_payload[0]["id"]

    approve_response = client.post(
        f"/api/v1/human-review/approve/{review_item_id}",
        json={"reviewer_notes": "Approved for sync"},
    )
    assert approve_response.status_code == 200

    generate_sync_response = client.post(f"/api/v1/notion-sync/generate/{run_id}")
    assert generate_sync_response.status_code == 200
    generate_sync_payload = generate_sync_response.json()
    assert generate_sync_payload["run_id"] == run_id
    assert generate_sync_payload["generated_count"] >= 1
    assert generate_sync_payload["pipeline_stage"] == "notion_sync_queue_ready"

    jobs_response = client.get(f"/api/v1/notion-sync?run_id={run_id}")
    assert jobs_response.status_code == 200
    jobs_payload = jobs_response.json()
    assert len(jobs_payload) >= 1
    sync_job_id = jobs_payload[0]["id"]
    assert jobs_payload[0]["sync_status"] == "pending_sync"

    mark_synced_response = client.post(
        f"/api/v1/notion-sync/mark-synced/{sync_job_id}",
        json={
            "notion_page_id": "notion-page-123",
            "sync_notes": "Synced successfully",
        },
    )
    assert mark_synced_response.status_code == 200
    mark_synced_payload = mark_synced_response.json()
    assert mark_synced_payload["sync_status"] == "synced"
    assert mark_synced_payload["notion_page_id"] == "notion-page-123"