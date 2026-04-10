from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_run_events_are_created_for_orchestrator_flow() -> None:
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

    dispatch_response = client.post(f"/api/v1/orchestrator/dispatch/{run_id}")
    assert dispatch_response.status_code == 200

    progress_response = client.post(
        f"/api/v1/orchestrator/progress/{run_id}",
        json={
            "pipeline_stage": "source_collection",
            "items_discovered": 4,
            "items_processed": 2,
            "orchestrator_notes": "Fetching source items",
        },
    )
    assert progress_response.status_code == 200

    complete_response = client.post(f"/api/v1/orchestrator/complete/{run_id}")
    assert complete_response.status_code == 200

    events_response = client.get(f"/api/v1/run-events/{run_id}")
    assert events_response.status_code == 200
    payload = events_response.json()
    assert len(payload) >= 3
    assert payload[0]["event_type"] == "dispatch"
    assert payload[-1]["event_type"] == "complete"


def test_recent_run_events_endpoint() -> None:
    response = client.get("/api/v1/run-events?limit=20")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)