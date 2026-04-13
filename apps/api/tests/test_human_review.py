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

    first_evidence_response = client.post(
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
            "metadata_json": {"source": "manual-test-1"},
        },
    )
    assert first_evidence_response.status_code == 201

    second_evidence_response = client.post(
        "/api/v1/evidence",
        json={
            "scrape_run_id": run_id,
            "source_name": "reddit",
            "platform_name": "99acres",
            "content_type": "comment",
            "raw_text": "The site is slow and pages keep loading for too long.",
            "cleaned_text": "The site is slow and pages keep loading for too long.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test-2"},
        },
    )
    assert second_evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200
    assert client.post(f"/api/v1/intelligence/{run_id}").status_code == 200

    generate_response = client.post(f"/api/v1/human-review/generate/{run_id}")
    assert generate_response.status_code == 200
    generate_payload = generate_response.json()
    assert generate_payload["run_id"] == run_id
    assert generate_payload["generated_count"] >= 2
    assert generate_payload["pipeline_stage"] == "human_review_queue_ready"

    summary_response = client.get(f"/api/v1/human-review/summary?run_id={run_id}")
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["run_id"] == run_id
    assert summary_payload["total_items"] >= 2
    assert summary_payload["pending_review_count"] >= 2

    queue_response = client.get(
        f"/api/v1/human-review?run_id={run_id}&include_details=true&limit=10&offset=0"
    )
    assert queue_response.status_code == 200
    queue_payload = queue_response.json()
    assert len(queue_payload) >= 2
    first_review_item_id = queue_payload[0]["id"]
    second_review_item_id = queue_payload[1]["id"]

    assert queue_payload[0]["review_status"] == "pending_review"
    assert queue_payload[0]["insight_snapshot"] is not None
    assert queue_payload[0]["evidence_snapshot"] is not None
    assert queue_payload[0]["insight_snapshot"]["pain_point_label"] is not None
    assert queue_payload[0]["evidence_snapshot"]["evidence_excerpt"] is not None

    detail_response = client.get(f"/api/v1/human-review/detail/{first_review_item_id}")
    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == first_review_item_id
    assert detail_payload["insight_snapshot"] is not None
    assert detail_payload["evidence_snapshot"] is not None

    approve_response = client.post(
        f"/api/v1/human-review/approve/{first_review_item_id}",
        json={"reviewer_notes": "Looks valid"},
    )
    assert approve_response.status_code == 200
    approve_payload = approve_response.json()
    assert approve_payload["review_status"] == "reviewed"
    assert approve_payload["reviewer_decision"] == "approved"
    assert approve_payload["reviewer_notes"] == "Looks valid"

    bulk_reject_response = client.post(
        "/api/v1/human-review/bulk/reject",
        json={
            "item_ids": [second_review_item_id],
            "reviewer_notes": "Duplicate complaint cluster",
        },
    )
    assert bulk_reject_response.status_code == 200
    bulk_reject_payload = bulk_reject_response.json()
    assert bulk_reject_payload["updated_count"] == 1
    assert bulk_reject_payload["reviewer_decision"] == "rejected"

    filtered_queue_response = client.get(
        f"/api/v1/human-review?run_id={run_id}&reviewer_decision=approved"
    )
    assert filtered_queue_response.status_code == 200
    filtered_queue_payload = filtered_queue_response.json()
    assert len(filtered_queue_payload) == 1
    assert filtered_queue_payload[0]["reviewer_decision"] == "approved"

    final_summary_response = client.get(f"/api/v1/human-review/summary?run_id={run_id}")
    assert final_summary_response.status_code == 200
    final_summary_payload = final_summary_response.json()
    assert final_summary_payload["approved_count"] == 1
    assert final_summary_payload["rejected_count"] == 1
    assert final_summary_payload["reviewed_count"] == 2