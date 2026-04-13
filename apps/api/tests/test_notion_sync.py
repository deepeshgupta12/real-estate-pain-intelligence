from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.integrations.notion_client import NotionClient
from app.main import app

client = TestClient(app)


def test_notion_sync_flow(monkeypatch) -> None:
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
    assert jobs_payload[0]["sync_status"] == "queued"
    assert jobs_payload[0]["idempotency_key"] is not None

    settings = get_settings()
    original_enable = settings.notion_enable_real_sync
    original_api_key = settings.notion_api_key
    original_database_id = settings.notion_database_id
    original_mode = settings.notion_destination_mode

    settings.notion_enable_real_sync = True
    settings.notion_api_key = "test-notion-key"
    settings.notion_database_id = "db-test-123"
    settings.notion_destination_mode = "database"

    def _mock_create_database_page(self, *, database_id: str, properties: dict, children: list):
        assert database_id == "db-test-123"
        assert "Name" in properties
        assert len(children) >= 2
        return {
            "id": "notion-page-123",
            "parent": {"database_id": database_id},
            "url": "https://www.notion.so/notion-page-123",
        }

    monkeypatch.setattr(NotionClient, "create_database_page", _mock_create_database_page)

    try:
        execute_response = client.post(f"/api/v1/notion-sync/execute/{sync_job_id}")
    finally:
        settings.notion_enable_real_sync = original_enable
        settings.notion_api_key = original_api_key
        settings.notion_database_id = original_database_id
        settings.notion_destination_mode = original_mode

    assert execute_response.status_code == 200
    execute_payload = execute_response.json()
    assert execute_payload["sync_status"] == "synced"
    assert execute_payload["notion_page_id"] == "notion-page-123"
    assert execute_payload["notion_database_id"] == "db-test-123"
    assert execute_payload["retry_count"] == 0