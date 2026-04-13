from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_intelligence import LLMIntelligenceService

client = TestClient(app)


def test_intelligence_processing_flow_deterministic_only() -> None:
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
            "raw_text": "The listings shown were outdated and the agent never called back.",
            "cleaned_text": "The listings shown were outdated and the agent never called back.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200

    intelligence_response = client.post(f"/api/v1/intelligence/{run_id}")
    assert intelligence_response.status_code == 200
    payload = intelligence_response.json()

    assert payload["run_id"] == run_id
    assert payload["total_evidence"] >= 1
    assert payload["insights_generated"] >= 1
    assert payload["llm_generated_count"] == 0
    assert payload["deterministic_generated_count"] >= 1
    assert payload["pipeline_stage"] == "intelligence_completed"

    insights_response = client.get(f"/api/v1/intelligence/{run_id}")
    assert insights_response.status_code == 200
    insights_payload = insights_response.json()
    assert len(insights_payload) >= 1
    assert insights_payload[0]["pain_point_label"] is not None
    assert insights_payload[0]["taxonomy_cluster"] is not None
    assert insights_payload[0]["priority_label"] is not None
    assert insights_payload[0]["action_recommendation"] is not None
    assert insights_payload[0]["metadata_json"]["analysis_mode"] == "deterministic_only"
    assert insights_payload[0]["metadata_json"]["llm_used"] is False


def test_intelligence_processing_flow_llm_assisted(monkeypatch) -> None:
    monkeypatch.setattr(LLMIntelligenceService, "is_enabled", staticmethod(lambda: True))

    def fake_generate_hybrid_fields(evidence, baseline_fields):
        enriched = dict(baseline_fields)
        enriched["pain_point_summary"] = "LLM refined summary for stale listings and callback issues."
        enriched["action_recommendation"] = "LLM suggests stronger freshness checks and callback SLA monitoring."
        enriched["confidence_score"] = "high"
        return enriched, {
            "llm_provider": "openai",
            "llm_model_name": "gpt-5.4",
            "llm_used": True,
            "llm_raw_output": '{"mocked": true}',
        }

    monkeypatch.setattr(
        LLMIntelligenceService,
        "generate_hybrid_fields",
        staticmethod(fake_generate_hybrid_fields),
    )

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
            "raw_text": "The property listing was outdated and no one called me back.",
            "cleaned_text": "The property listing was outdated and no one called me back.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200

    intelligence_response = client.post(f"/api/v1/intelligence/{run_id}")
    assert intelligence_response.status_code == 200
    payload = intelligence_response.json()

    assert payload["llm_generated_count"] >= 1
    assert payload["deterministic_generated_count"] == 0

    insights_response = client.get(f"/api/v1/intelligence/{run_id}")
    assert insights_response.status_code == 200
    insights_payload = insights_response.json()
    assert insights_payload[0]["metadata_json"]["analysis_mode"] == "llm_assisted"
    assert insights_payload[0]["metadata_json"]["llm_used"] is True
    assert insights_payload[0]["confidence_score"] == "high"
    assert "LLM refined summary" in insights_payload[0]["pain_point_summary"]


def test_intelligence_processing_flow_llm_fallback(monkeypatch) -> None:
    monkeypatch.setattr(LLMIntelligenceService, "is_enabled", staticmethod(lambda: True))

    def failing_generate_hybrid_fields(evidence, baseline_fields):
        raise RuntimeError("simulated llm failure")

    monkeypatch.setattr(
        LLMIntelligenceService,
        "generate_hybrid_fields",
        staticmethod(failing_generate_hybrid_fields),
    )

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

    evidence_response = client.post(
        "/api/v1/evidence",
        json={
            "scrape_run_id": run_id,
            "source_name": "reddit",
            "platform_name": "Housing.com",
            "content_type": "comment",
            "raw_text": "The page was slow and filters took too long to respond.",
            "cleaned_text": "The page was slow and filters took too long to respond.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200

    intelligence_response = client.post(f"/api/v1/intelligence/{run_id}")
    assert intelligence_response.status_code == 200
    payload = intelligence_response.json()

    assert payload["llm_generated_count"] == 0
    assert payload["deterministic_generated_count"] >= 1

    insights_response = client.get(f"/api/v1/intelligence/{run_id}")
    assert insights_response.status_code == 200
    insights_payload = insights_response.json()
    assert insights_payload[0]["metadata_json"]["analysis_mode"] == "deterministic_fallback"
    assert insights_payload[0]["metadata_json"]["llm_used"] is False
    assert insights_payload[0]["metadata_json"]["llm_attempted"] is True
    assert insights_payload[0]["metadata_json"]["llm_error"] == "simulated llm failure"