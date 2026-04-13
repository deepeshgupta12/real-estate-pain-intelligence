from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_retrieval_index_and_search_flow() -> None:
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
            "raw_text": "The property listing is outdated and the agent did not respond.",
            "cleaned_text": "The property listing is outdated and the agent did not respond.",
            "language": "en",
            "is_relevant": True,
            "metadata_json": {"source": "manual-test"},
        },
    )
    assert evidence_response.status_code == 201

    assert client.post(f"/api/v1/normalization/{run_id}").status_code == 200
    assert client.post(f"/api/v1/multilingual/{run_id}").status_code == 200
    assert client.post(f"/api/v1/intelligence/{run_id}").status_code == 200

    index_response = client.post(f"/api/v1/retrieval/index/{run_id}")
    assert index_response.status_code == 200
    index_payload = index_response.json()
    assert index_payload["run_id"] == run_id
    assert index_payload["indexed_count"] >= 1
    assert index_payload["pipeline_stage"] == "retrieval_indexed"

    documents_response = client.get(f"/api/v1/retrieval/{run_id}")
    assert documents_response.status_code == 200
    documents_payload = documents_response.json()
    assert len(documents_payload) >= 1
    assert documents_payload[0]["retrieval_status"] == "indexed"
    assert documents_payload[0]["embedding_status"] == "embedded"
    assert documents_payload[0]["embedding_model_name"] == "hash-embedding-v1"
    assert documents_payload[0]["embedding_dimensions"] == 64
    assert documents_payload[0]["embedded_at"] is not None

    search_response = client.post(
        "/api/v1/retrieval/search",
        json={
            "query": "outdated listing agent response",
            "top_k": 5,
            "run_id": run_id,
        },
    )
    assert search_response.status_code == 200
    search_payload = search_response.json()
    assert len(search_payload) >= 1
    assert search_payload[0]["score"] > 0
    assert search_payload[0]["score_type"] == "vector_cosine_similarity"
    assert search_payload[0]["document_text"] is not None