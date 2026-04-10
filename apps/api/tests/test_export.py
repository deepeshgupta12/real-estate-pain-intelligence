from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_export_flow() -> None:
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
            "raw_text": "The listing looked outdated and page loading was slow.",
            "cleaned_text": "The listing looked outdated and page loading was slow.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200
    assert client.post(f"/api/v1/intelligence/{run_id}").status_code == 200

    generate_response = client.post(
        f"/api/v1/exports/generate/{run_id}",
        json={"export_formats": ["csv", "json", "pdf"]},
    )
    assert generate_response.status_code == 200
    generate_payload = generate_response.json()
    assert generate_payload["run_id"] == run_id
    assert generate_payload["generated_count"] == 3
    assert generate_payload["pipeline_stage"] == "export_queue_ready"

    jobs_response = client.get(f"/api/v1/exports?run_id={run_id}")
    assert jobs_response.status_code == 200
    jobs_payload = jobs_response.json()
    assert len(jobs_payload) == 3

    export_job_id = jobs_payload[0]["id"]

    completed_response = client.post(
        f"/api/v1/exports/mark-completed/{export_job_id}",
        json={
            "file_name": "run-export.csv",
            "file_path": "/tmp/run-export.csv",
            "export_notes": "Export generated successfully",
        },
    )
    assert completed_response.status_code == 200
    completed_payload = completed_response.json()
    assert completed_payload["export_status"] == "completed"
    assert completed_payload["file_name"] == "run-export.csv"