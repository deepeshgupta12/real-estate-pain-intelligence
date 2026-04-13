"""Tests for multi-agent orchestrator service."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.agent_orchestrator import (
    AgentOrchestratorService,
    _deterministic_fallback,
    AGENT_TOOLS,
    AGENT_CHAIN,
)


class TestDeterministicFallback:
    def test_returns_all_required_keys(self):
        result = _deterministic_fallback("slow app keeps crashing", {})
        assert "classification" in result
        assert "pain_point" in result
        assert "root_cause" in result
        assert "competitor" in result
        assert "action" in result
        assert result["method"] == "deterministic_fallback"

    def test_platform_performance_for_slow_text(self):
        result = _deterministic_fallback("the app is extremely slow", {})
        assert result["pain_point"]["taxonomy_cluster"] == "platform_performance"
        assert result["classification"]["journey_stage"] is not None

    def test_trust_issue_for_fraud_text(self):
        result = _deterministic_fallback("I was cheated with a fake listing scam", {})
        assert result["pain_point"]["taxonomy_cluster"] == "trust_and_safety"
        assert result["pain_point"]["priority_label"] == "high"

    def test_agent_unresponsive_for_callback_text(self):
        result = _deterministic_fallback("agent never replied to my callback", {})
        assert result["pain_point"]["taxonomy_cluster"] == "lead_management"
        assert result["pain_point"]["priority_label"] == "high"

    def test_competitor_detection(self):
        result = _deterministic_fallback("99acres is better than this platform", {})
        assert result["competitor"]["competitor_label"] == "99acres"
        assert result["competitor"]["comparison_direction"] != "no_comparison"

    def test_no_competitor_for_generic_text(self):
        result = _deterministic_fallback("the search filter is broken", {})
        assert result["competitor"]["competitor_label"] == "none"
        assert result["competitor"]["comparison_direction"] == "no_comparison"

    def test_agents_executed_list(self):
        result = _deterministic_fallback("something went wrong", {})
        assert isinstance(result["agents_executed"], list)
        assert len(result["agents_executed"]) == len(AGENT_CHAIN)


class TestAgentToolsSchema:
    def test_all_tools_have_required_fields(self):
        required_fields = {"name", "description", "input_schema"}
        for tool in AGENT_TOOLS:
            assert required_fields.issubset(set(tool.keys()))

    def test_five_agents_defined(self):
        assert len(AGENT_TOOLS) == 5

    def test_agent_chain_matches_tool_names(self):
        tool_names = {t["name"] for t in AGENT_TOOLS}
        assert set(AGENT_CHAIN) == tool_names


class TestAgentOrchestratorService:
    def test_analyse_returns_deterministic_when_not_enabled(self):
        with patch.object(AgentOrchestratorService, "is_enabled", return_value=False):
            result = AgentOrchestratorService.analyse(
                "property listing is outdated and wrong price",
                context={"source_name": "reddit", "platform_name": "99acres"},
            )
        assert "pain_point" in result
        assert result["method"] == "deterministic_fallback"

    def test_analyse_uses_cache_on_second_call(self):
        text = "unique evidence for cache test xyz123"
        with patch.object(AgentOrchestratorService, "is_enabled", return_value=False):
            result1 = AgentOrchestratorService.analyse(text, use_cache=True)
            result2 = AgentOrchestratorService.analyse(text, use_cache=True)
        assert result2.get("_cache_hit") is True

    def test_analyse_batch_processes_all_items(self):
        items = [
            {"evidence_id": 1, "text": "the app crashes constantly", "context": {}},
            {"evidence_id": 2, "text": "agent never responds to callbacks", "context": {}},
            {"evidence_id": 3, "text": "fake listing on platform", "context": {}},
        ]
        with patch.object(AgentOrchestratorService, "is_enabled", return_value=False):
            results = AgentOrchestratorService.analyse_batch(items)
        assert len(results) == 3
        for r in results:
            assert "pain_point" in r

    def test_get_agent_status_returns_expected_keys(self):
        status = AgentOrchestratorService.get_agent_status()
        assert "anthropic_sdk_available" in status
        assert "orchestrator_enabled" in status
        assert "agents" in status
        assert "fallback_available" in status
        assert status["fallback_available"] is True

    def test_analyse_batch_respects_max_items(self):
        items = [{"evidence_id": i, "text": f"issue {i}", "context": {}} for i in range(20)]
        with patch.object(AgentOrchestratorService, "is_enabled", return_value=False):
            results = AgentOrchestratorService.analyse_batch(items, max_items=5)
        assert len(results) <= 5


class TestAgentOrchestrationEndpoints:
    def test_status_endpoint(self, client):
        resp = client.get("/api/v1/agent-orchestration/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "orchestrator_enabled" in data
        assert "agents" in data

    def test_analyse_endpoint(self, client):
        resp = client.post(
            "/api/v1/agent-orchestration/analyse",
            json={"text": "the app is slow and agent never responds", "context": {}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pain_point" in data

    def test_analyse_endpoint_short_text(self, client):
        resp = client.post(
            "/api/v1/agent-orchestration/analyse",
            json={"text": "x"},
        )
        assert resp.status_code == 422  # validation error

    def test_batch_endpoint(self, client):
        resp = client.post(
            "/api/v1/agent-orchestration/analyse-batch",
            json={
                "items": [
                    {"text": "app crashes constantly", "context": {}},
                    {"text": "fake listing scam", "context": {}},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    def test_run_orchestration_not_found(self, client):
        resp = client.post("/api/v1/agent-orchestration/run/99999")
        assert resp.status_code == 404
