from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_final_hardening_readiness_and_overview() -> None:
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

    assert client.post(f"/api/v1/scrape-execution/{run_id}").status_code == 200
    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200
    assert client.post(f"/api/v1/intelligence/{run_id}").status_code == 200
    assert client.post(f"/api/v1/retrieval/index/{run_id}").status_code == 200
    assert client.post(f"/api/v1/human-review/generate/{run_id}").status_code == 200

    summary_response = client.get(f"/api/v1/human-review/summary?run_id={run_id}")
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["total_items"] >= 1
    assert summary_payload["pending_review_count"] >= 1

    queue_response = client.get(f"/api/v1/human-review?run_id={run_id}")
    assert queue_response.status_code == 200
    review_item_id = queue_response.json()[0]["id"]

    approve_response = client.post(
        f"/api/v1/human-review/approve/{review_item_id}",
        json={"reviewer_notes": "Looks good"},
    )
    assert approve_response.status_code == 200

    assert client.post(f"/api/v1/notion-sync/generate/{run_id}").status_code == 200
    assert (
        client.post(
            f"/api/v1/exports/generate/{run_id}",
            json={"export_formats": ["csv", "json"]},
        ).status_code
        == 200
    )

    readiness_response = client.get(f"/api/v1/final-hardening/readiness/{run_id}")
    assert readiness_response.status_code == 200
    readiness_payload = readiness_response.json()
    assert readiness_payload["run_id"] == run_id
    assert readiness_payload["checks"]["has_evidence"] is True
    assert readiness_payload["checks"]["human_review_ready"] is True
    assert readiness_payload["checks"]["review_console_ready"] is True
    assert readiness_payload["checks"]["notion_ready"] is True
    assert readiness_payload["counts"]["evidence_count"] >= 1
    assert readiness_payload["counts"]["insight_count"] >= 1
    assert readiness_payload["counts"]["review_count"] >= 1
    assert readiness_payload["counts"]["approved_review_count"] == 1
    assert readiness_payload["counts"]["export_count"] == 2

    overview_response = client.get("/api/v1/final-hardening/overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert overview_payload["runs_total"] >= 1
    assert overview_payload["evidence_total"] >= 1
    assert overview_payload["insights_total"] >= 1
    assert overview_payload["review_queue_total"] >= 1
    assert overview_payload["approved_review_total"] >= 1


def test_final_hardening_guardrails_block_downstream_without_prerequisites() -> None:
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

    retrieval_response = client.post(f"/api/v1/retrieval/index/{run_id}")
    assert retrieval_response.status_code == 400
    assert "no evidence" in retrieval_response.json()["detail"].lower()

    export_response = client.post(
        f"/api/v1/exports/generate/{run_id}",
        json={"export_formats": ["csv"]},
    )
    assert export_response.status_code == 400
    assert "no evidence" in export_response.json()["detail"].lower()