from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_orchestrator_dispatch_start_progress_complete_flow() -> None:
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

    dispatch_response = client.post(f"/api/v1/orchestrator/dispatch/{run_id}")
    assert dispatch_response.status_code == 200
    assert dispatch_response.json()["status"] == "queued"
    assert dispatch_response.json()["pipeline_stage"] == "dispatched"

    start_response = client.post(f"/api/v1/orchestrator/start/{run_id}")
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "running"
    assert start_response.json()["pipeline_stage"] == "ingestion"

    progress_response = client.post(
        f"/api/v1/orchestrator/progress/{run_id}",
        json={
            "pipeline_stage": "source_collection",
            "items_discovered": 20,
            "items_processed": 8,
            "orchestrator_notes": "Source pull in progress",
        },
    )
    assert progress_response.status_code == 200
    assert progress_response.json()["status"] == "running"
    assert progress_response.json()["pipeline_stage"] == "source_collection"

    queue_response = client.get("/api/v1/orchestrator/queue")
    assert queue_response.status_code == 200
    assert isinstance(queue_response.json(), list)
    assert len(queue_response.json()) >= 1

    complete_response = client.post(f"/api/v1/orchestrator/complete/{run_id}")
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"
    assert complete_response.json()["pipeline_stage"] == "completed"


def test_orchestrator_fail_flow() -> None:
    run_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "youtube",
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

    fail_response = client.post(
        f"/api/v1/orchestrator/fail/{run_id}",
        json={
            "error_message": "Source rate limited during comment fetch",
            "orchestrator_notes": "Retry required",
        },
    )
    assert fail_response.status_code == 200
    assert fail_response.json()["status"] == "failed"
    assert fail_response.json()["pipeline_stage"] == "failed"