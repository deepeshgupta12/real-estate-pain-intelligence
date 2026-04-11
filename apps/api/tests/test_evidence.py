from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_list_raw_evidence() -> None:
    run_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "youtube",
            "target_brand": "Magicbricks",
            "status": "created",
            "items_discovered": 5,
            "items_processed": 0,
        },
    )
    assert run_response.status_code == 201
    run_id = run_response.json()["id"]

    evidence_response = client.post(
        "/api/v1/evidence",
        json={
            "scrape_run_id": run_id,
            "source_name": "youtube",
            "platform_name": "Magicbricks",
            "content_type": "comment",
            "raw_text": "The listings shown were outdated and the response was slow.",
            "cleaned_text": "The listings shown were outdated and the response was slow.",
            "language": "en",
            "fetched_at": "2026-04-11T12:00:00Z",
            "source_query": "Magicbricks project review",
            "parser_version": "manual-v1",
            "dedupe_key": "manual-dedupe-key",
            "raw_payload_json": {"video_id": "abc123", "manual": True},
            "is_relevant": True,
            "metadata_json": {"video_id": "abc123"},
        },
    )
    assert evidence_response.status_code == 201
    created_payload = evidence_response.json()
    assert created_payload["platform_name"] == "Magicbricks"
    assert created_payload["content_type"] == "comment"
    assert created_payload["source_query"] == "Magicbricks project review"
    assert created_payload["parser_version"] == "manual-v1"
    assert created_payload["dedupe_key"] == "manual-dedupe-key"

    list_response = client.get("/api/v1/evidence")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert isinstance(payload, list)
    assert len(payload) >= 1