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


def test_recent_run_events_endpoint_and_filters() -> None:
    run_response = client.post(
        "/api/v1/runs",
        json={
            "source_name": "youtube",
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

    assert client.post(f"/api/v1/orchestrator/dispatch/{run_id}").status_code == 200
    assert (
        client.post(
            f"/api/v1/orchestrator/progress/{run_id}",
            json={
                "pipeline_stage": "source_collection",
                "items_discovered": 10,
                "items_processed": 3,
                "orchestrator_notes": "Source fetch in progress",
            },
        ).status_code
        == 200
    )
    assert client.post(f"/api/v1/orchestrator/complete/{run_id}").status_code == 200

    response = client.get("/api/v1/run-events?limit=20")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)

    filtered_response = client.get(
        f"/api/v1/run-events?run_id={run_id}&event_type=progress&stage=source_collection"
    )
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert len(filtered_payload) == 1
    assert filtered_payload[0]["event_type"] == "progress"
    assert filtered_payload[0]["stage"] == "source_collection"

    ascending_response = client.get(f"/api/v1/run-events/{run_id}?newest_first=false")
    assert ascending_response.status_code == 200
    ascending_payload = ascending_response.json()
    assert ascending_payload[0]["event_type"] == "dispatch"
    assert ascending_payload[-1]["event_type"] == "complete"