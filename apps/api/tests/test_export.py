from pathlib import Path

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

    formats = {job["export_format"] for job in jobs_payload}
    assert formats == {"csv", "json", "pdf"}

    for job in jobs_payload:
        assert job["export_status"] == "completed"
        assert job["file_name"] is not None
        assert job["file_path"] is not None
        assert job["file_size_bytes"] is not None
        assert job["file_size_bytes"] > 0
        assert job["row_count"] is not None
        assert job["generated_at"] is not None
        assert isinstance(job["summary_json"], dict)
        assert isinstance(job["artifact_metadata_json"], dict)

        export_path = Path(job["file_path"])
        assert export_path.exists()
        assert export_path.is_file()

    csv_job = next(job for job in jobs_payload if job["export_format"] == "csv")
    json_job = next(job for job in jobs_payload if job["export_format"] == "json")
    pdf_job = next(job for job in jobs_payload if job["export_format"] == "pdf")

    assert csv_job["row_count"] >= 1
    assert json_job["row_count"] >= 1
    assert pdf_job["row_count"] >= 1

    completed_response = client.post(
        f"/api/v1/exports/mark-completed/{csv_job['id']}",
        json={
            "file_name": csv_job["file_name"],
            "file_path": csv_job["file_path"],
            "file_size_bytes": csv_job["file_size_bytes"],
            "row_count": csv_job["row_count"],
            "artifact_metadata_json": csv_job["artifact_metadata_json"],
            "export_notes": "Manual completion confirmation",
        },
    )
    assert completed_response.status_code == 200
    completed_payload = completed_response.json()
    assert completed_payload["export_status"] == "completed"
    assert completed_payload["export_notes"] == "Manual completion confirmation"