from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_multilingual_processing_flow() -> None:
    run_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "reddit",
            "target_brand": "Magicbricks",
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
            "platform_name": "Magicbricks",
            "content_type": "comment",
            "raw_text": "यह प्रॉपर्टी लिस्टिंग पुरानी है और एजेंट जवाब नहीं देता",
            "cleaned_text": "यह प्रॉपर्टी लिस्टिंग पुरानी है और एजेंट जवाब नहीं देता",
            "language": "hi",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    normalization_response = client.post(f"/api/v1/normalization/{run_id}")
    assert normalization_response.status_code == 200

    multilingual_response = client.post(f"/api/v1/multilingual/{run_id}")
    assert multilingual_response.status_code == 200
    payload = multilingual_response.json()

    assert payload["run_id"] == run_id
    assert payload["total_evidence"] >= 1
    assert payload["processed_count"] >= 1
    assert payload["pipeline_stage"] == "multilingual_completed"

    summary_response = client.get(f"/api/v1/multilingual/{run_id}")
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert len(summary_payload) >= 1
    assert summary_payload[0]["resolved_language"] == "hi"
    assert summary_payload[0]["script_label"] == "devanagari"
    assert summary_payload[0]["multilingual_status"] == "processed"
    assert summary_payload[0]["bridge_text"] is not None


def test_evidence_endpoint_returns_multilingual_fields() -> None:
    response = client.get("/api/v1/evidence")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    if payload:
        assert "resolved_language" in payload[0]
        assert "language_family" in payload[0]
        assert "script_label" in payload[0]
        assert "multilingual_status" in payload[0]
        assert "multilingual_notes" in payload[0]
        assert "bridge_text" in payload[0]