from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.scrape_run import ScrapeRun

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
    queue_payload = queue_response.json()
    assert isinstance(queue_payload, list)
    assert len(queue_payload) >= 1
    queue_item = next(item for item in queue_payload if item["run_id"] == run_id)
    assert queue_item["is_stale"] is False
    assert queue_item["health_label"] in {"healthy", "waiting"}

    complete_response = client.post(f"/api/v1/orchestrator/complete/{run_id}")
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "completed"
    assert complete_response.json()["pipeline_stage"] == "completed"


def test_orchestrator_fail_flow_and_diagnostics() -> None:
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

    assert client.post(f"/api/v1/orchestrator/dispatch/{run_id}").status_code == 200
    assert client.post(f"/api/v1/orchestrator/start/{run_id}").status_code == 200
    assert (
        client.post(
            f"/api/v1/orchestrator/progress/{run_id}",
            json={
                "pipeline_stage": "source_collection",
                "items_discovered": 5,
                "items_processed": 2,
                "orchestrator_notes": "Comments fetch running",
            },
        ).status_code
        == 200
    )

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

    diagnostics_response = client.get(f"/api/v1/orchestrator/diagnostics/{run_id}")
    assert diagnostics_response.status_code == 200
    diagnostics_payload = diagnostics_response.json()
    assert diagnostics_payload["run_id"] == run_id
    assert diagnostics_payload["failure_snapshot"]["failed"] is True
    assert diagnostics_payload["failure_snapshot"]["failed_stage"] == "failed"
    assert diagnostics_payload["failure_snapshot"]["last_successful_stage"] == "source_collection"
    assert diagnostics_payload["latest_event"]["event_type"] == "fail"
    assert diagnostics_payload["total_events"] >= 4


def test_orchestrator_queue_and_diagnostics_flag_stale_runs() -> None:
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

    assert client.post(f"/api/v1/orchestrator/dispatch/{run_id}").status_code == 200
    assert client.post(f"/api/v1/orchestrator/start/{run_id}").status_code == 200

    with SessionLocal() as db:
        run = db.get(ScrapeRun, run_id)
        assert run is not None
        run.status = "running"
        run.pipeline_stage = "source_collection"
        run.last_heartbeat_at = datetime.now(timezone.utc) - timedelta(hours=1)
        run.orchestrator_notes = "Heartbeat intentionally backdated for stale-run test"
        db.commit()

    queue_response = client.get("/api/v1/orchestrator/queue")
    assert queue_response.status_code == 200
    queue_payload = queue_response.json()
    queue_item = next(item for item in queue_payload if item["run_id"] == run_id)
    assert queue_item["is_stale"] is True
    assert queue_item["health_label"] == "stale"
    assert queue_item["heartbeat_age_seconds"] is not None
    assert queue_item["heartbeat_age_seconds"] > 900

    diagnostics_response = client.get(f"/api/v1/orchestrator/diagnostics/{run_id}")
    assert diagnostics_response.status_code == 200
    diagnostics_payload = diagnostics_response.json()
    assert diagnostics_payload["is_stale"] is True
    assert diagnostics_payload["health_label"] == "stale"