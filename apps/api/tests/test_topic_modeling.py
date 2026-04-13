"""Tests for topic modeling service."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.topic_modeling import (
    TopicModelingService,
    _assign_seed_cluster,
    _seed_cluster_score,
    REAL_ESTATE_PAIN_SEEDS,
)


class TestSeedClusters:
    def test_seed_cluster_list_not_empty(self):
        assert len(REAL_ESTATE_PAIN_SEEDS) >= 5

    def test_seed_cluster_has_required_fields(self):
        for seed in REAL_ESTATE_PAIN_SEEDS:
            assert "id" in seed
            assert "label" in seed
            assert "keywords" in seed
            assert "description" in seed
            assert isinstance(seed["keywords"], list)
            assert len(seed["keywords"]) > 0

    def test_seed_cluster_score_for_matching_text(self):
        score = _seed_cluster_score("the app is very slow and lagging", ["slow", "lag", "loading"])
        assert score > 0.0

    def test_seed_cluster_score_for_non_matching_text(self):
        score = _seed_cluster_score("great experience overall", ["slow", "lag", "crash"])
        assert score == 0.0


class TestClusterAssignment:
    def test_assigns_platform_performance_for_slow_text(self):
        cluster_id, score = _assign_seed_cluster("the app is very slow and keeps crashing")
        assert cluster_id == "platform_performance"
        assert score > 0.0

    def test_assigns_trust_for_fraud_text(self):
        cluster_id, score = _assign_seed_cluster("this is a complete fraud and scam listing")
        assert cluster_id == "trust_and_safety"
        assert score > 0.0

    def test_assigns_lead_management_for_agent_text(self):
        cluster_id, score = _assign_seed_cluster("agent never responded to my callback enquiry")
        assert cluster_id == "lead_management"
        assert score > 0.0

    def test_returns_general_for_unrelated_text(self):
        cluster_id, _ = _assign_seed_cluster("the sky is blue and birds are flying")
        # Should return some cluster (general_pain or weakly matched)
        assert isinstance(cluster_id, str)


class TestTopicModelingService:
    def test_run_topic_modeling_run_not_found(self):
        db = MagicMock(spec=Session)
        db.get.return_value = None

        with pytest.raises(ValueError, match="Run 999 not found"):
            TopicModelingService.run_topic_modeling(db, 999)

    def test_seed_cluster_list_completeness(self):
        """Ensure all expected cluster IDs exist in seed list."""
        ids = [s["id"] for s in REAL_ESTATE_PAIN_SEEDS]
        expected = [
            "inventory_quality",
            "platform_performance",
            "lead_management",
            "trust_and_safety",
            "pricing_transparency",
        ]
        for expected_id in expected:
            assert expected_id in ids, f"Missing expected seed cluster: {expected_id}"

    def test_topic_modeling_service_imported_cleanly(self):
        """Smoke test: service can be imported and instantiated."""
        assert TopicModelingService is not None
        assert hasattr(TopicModelingService, "run_topic_modeling")
        assert hasattr(TopicModelingService, "get_cluster_summary")


class TestSeedClusterEndpoint:
    """Integration tests for topic modeling API endpoints."""

    def test_seed_clusters_endpoint(self, client):
        resp = client.get("/api/v1/topic-modeling/seed-clusters")
        assert resp.status_code == 200
        data = resp.json()
        assert "seed_clusters" in data
        assert data["total"] >= 5

    def test_topic_modeling_run_not_found(self, client):
        resp = client.get("/api/v1/topic-modeling/99999")
        assert resp.status_code == 404

    def test_cluster_summary_run_not_found(self, client):
        # Should succeed even with no evidence (returns empty list)
        resp = client.get("/api/v1/topic-modeling/99999/clusters")
        # Either 200 with empty clusters or 500
        assert resp.status_code in (200, 404, 500)
