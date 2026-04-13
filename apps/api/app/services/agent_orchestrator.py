"""
Multi-agent orchestration service.

Implements a structured tool_use-based agent pipeline with 5 specialized agents:

  1. EvidenceClassifier   — classifies evidence type and journey stage
  2. PainPointExtractor   — extracts specific pain point label and summary
  3. RootCauseAnalyst     — hypothesises root cause from classified evidence
  4. CompetitorBenchmarker — identifies competitive context
  5. ActionAdvisor        — recommends product action

The orchestrator routes evidence through these agents using Anthropic's
tool_use pattern, accumulating structured outputs at each hop.

Falls back to rule-based deterministic output when Anthropic SDK is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import get_settings
from app.services.llm_cache import LLMResponseCache

logger = logging.getLogger(__name__)
_cache = LLMResponseCache()

# ---------------------------------------------------------------------------
# Optional Anthropic SDK import
# ---------------------------------------------------------------------------
try:
    import anthropic as _anthropic_sdk

    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False
    logger.info("anthropic SDK not installed; agent orchestrator will use deterministic fallback")


# ---------------------------------------------------------------------------
# Agent tool definitions (used in tool_use calls)
# ---------------------------------------------------------------------------

AGENT_TOOLS = [
    {
        "name": "classify_evidence",
        "description": (
            "Classify a piece of real-estate user feedback. "
            "Determine the evidence type (complaint, praise, question, neutral) "
            "and the journey stage (discovery, consideration, conversion, post_discovery)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "evidence_type": {
                    "type": "string",
                    "enum": ["complaint", "praise", "question", "neutral"],
                    "description": "The primary type of evidence.",
                },
                "journey_stage": {
                    "type": "string",
                    "enum": ["discovery", "consideration", "conversion", "post_discovery"],
                    "description": "The real-estate journey stage this feedback belongs to.",
                },
                "sentiment_polarity": {
                    "type": "string",
                    "enum": ["positive", "neutral", "negative"],
                    "description": "Overall sentiment polarity of the feedback.",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Confidence in this classification.",
                },
            },
            "required": ["evidence_type", "journey_stage", "sentiment_polarity", "confidence"],
        },
    },
    {
        "name": "extract_pain_point",
        "description": (
            "Extract the specific pain point from user feedback. "
            "Produce a structured label, a one-sentence summary, "
            "and a taxonomy cluster category."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pain_point_label": {
                    "type": "string",
                    "description": "Snake-case label for the pain point, e.g. 'outdated_listing'.",
                },
                "pain_point_summary": {
                    "type": "string",
                    "description": "One-sentence plain-language summary of the pain point.",
                },
                "taxonomy_cluster": {
                    "type": "string",
                    "enum": [
                        "inventory_quality",
                        "platform_performance",
                        "lead_management",
                        "trust_and_safety",
                        "pricing_transparency",
                        "search_discovery",
                        "transaction_process",
                        "ux_design",
                        "general_product_experience",
                    ],
                    "description": "High-level taxonomy cluster this pain point belongs to.",
                },
                "priority_label": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Suggested priority for addressing this pain point.",
                },
            },
            "required": ["pain_point_label", "pain_point_summary", "taxonomy_cluster", "priority_label"],
        },
    },
    {
        "name": "analyse_root_cause",
        "description": (
            "Generate a root cause hypothesis for an identified pain point. "
            "Consider the source, platform, and classification context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "root_cause_hypothesis": {
                    "type": "string",
                    "description": "Concise root cause hypothesis (1-2 sentences).",
                },
                "affected_system": {
                    "type": "string",
                    "description": "The product/engineering system most likely responsible (e.g. 'listing_refresh_pipeline').",
                },
                "hypothesis_confidence": {
                    "type": "string",
                    "enum": ["speculative", "plausible", "likely"],
                    "description": "Confidence level of the root cause hypothesis.",
                },
            },
            "required": ["root_cause_hypothesis", "affected_system", "hypothesis_confidence"],
        },
    },
    {
        "name": "benchmark_competitor",
        "description": (
            "Identify competitive context for the feedback. "
            "Determine which competitor platform is referenced or implicitly compared against."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "competitor_label": {
                    "type": "string",
                    "description": "Normalized competitor label, e.g. '99acres', 'magicbricks', 'none'.",
                },
                "comparison_direction": {
                    "type": "string",
                    "enum": ["favours_competitor", "favours_us", "neutral", "no_comparison"],
                    "description": "Direction of the implicit or explicit comparison.",
                },
                "competitive_signal": {
                    "type": "string",
                    "description": "One-sentence summary of the competitive signal, if any.",
                },
            },
            "required": ["competitor_label", "comparison_direction", "competitive_signal"],
        },
    },
    {
        "name": "recommend_action",
        "description": (
            "Recommend a product or operational action to address the identified pain point. "
            "Be specific, actionable, and concise."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action_recommendation": {
                    "type": "string",
                    "description": "Specific action recommendation for the product or engineering team.",
                },
                "action_type": {
                    "type": "string",
                    "enum": ["product_fix", "engineering_fix", "process_fix", "investigation", "monitoring"],
                    "description": "Category of the recommended action.",
                },
                "effort_estimate": {
                    "type": "string",
                    "enum": ["quick_win", "medium_term", "long_term"],
                    "description": "Rough effort estimate for the action.",
                },
            },
            "required": ["action_recommendation", "action_type", "effort_estimate"],
        },
    },
]

# Mapping from tool name to the next agent in the chain
AGENT_CHAIN = [
    "classify_evidence",
    "extract_pain_point",
    "analyse_root_cause",
    "benchmark_competitor",
    "recommend_action",
]


# ---------------------------------------------------------------------------
# Deterministic fallback
# ---------------------------------------------------------------------------

def _deterministic_fallback(evidence_text: str, context: dict[str, Any]) -> dict[str, Any]:
    """Rule-based fallback when Anthropic SDK is not available."""
    text = evidence_text.lower()

    # Journey stage
    if any(t in text for t in ["search", "discover", "listing", "filter", "find"]):
        journey_stage = "discovery"
    elif any(t in text for t in ["agent", "contact", "enquir", "callback"]):
        journey_stage = "consideration"
    elif any(t in text for t in ["payment", "loan", "booking", "visit", "deal"]):
        journey_stage = "conversion"
    else:
        journey_stage = "post_discovery"

    # Pain point — trust/fraud checked first (highest priority signal)
    if any(t in text for t in ["fraud", "scam", "fake", "spam", "cheat"]):
        label, summary, cluster = "trust_issue", "User encountered fraudulent or misleading content.", "trust_and_safety"
    elif any(t in text for t in ["outdated", "wrong", "old", "stale", "fake listing"]):
        label, summary, cluster = "outdated_listing", "User encountered outdated or inaccurate listing.", "inventory_quality"
    elif any(t in text for t in ["slow", "lag", "loading", "crash", "timeout"]):
        label, summary, cluster = "slow_platform", "User experienced performance or reliability issues.", "platform_performance"
    elif any(t in text for t in ["agent", "no reply", "unresponsive", "callback"]):
        label, summary, cluster = "agent_unresponsive", "User did not receive timely agent response.", "lead_management"
    elif any(t in text for t in ["price", "hidden", "charge", "fee", "expensive"]):
        label, summary, cluster = "pricing_concern", "User is concerned about pricing transparency.", "pricing_transparency"
    else:
        label, summary, cluster = "general_issue", "User reported a general product experience issue.", "general_product_experience"

    # Priority
    if cluster in ("trust_and_safety", "lead_management"):
        priority = "high"
    elif cluster in ("inventory_quality", "platform_performance"):
        priority = "medium"
    else:
        priority = "low"

    # Competitor
    competitor = "none"
    for comp in ["99acres", "magicbricks", "housing", "nobroker", "commonfloor", "squareyards"]:
        if comp in text.replace(" ", "").replace(".", ""):
            competitor = comp
            break

    cause_map = {
        "inventory_quality": "Listing refresh pipeline may be delayed or inconsistent.",
        "platform_performance": "Frontend or API latency may be causing degraded experience.",
        "lead_management": "Lead routing or agent notification workflow may be weak.",
        "trust_and_safety": "Verification or moderation pipeline may be insufficient.",
        "pricing_transparency": "Pricing display or disclosure logic may be incomplete.",
    }
    root_cause = cause_map.get(cluster, "Requires deeper investigation and user signal clustering.")

    return {
        "classification": {
            "evidence_type": "complaint",
            "journey_stage": journey_stage,
            "sentiment_polarity": "negative",
            "confidence": "medium",
        },
        "pain_point": {
            "pain_point_label": label,
            "pain_point_summary": summary,
            "taxonomy_cluster": cluster,
            "priority_label": priority,
        },
        "root_cause": {
            "root_cause_hypothesis": root_cause,
            "affected_system": cluster,
            "hypothesis_confidence": "plausible",
        },
        "competitor": {
            "competitor_label": competitor,
            "comparison_direction": "no_comparison" if competitor == "none" else "neutral",
            "competitive_signal": f"No direct competitor comparison detected." if competitor == "none" else f"Competitor '{competitor}' mentioned in feedback.",
        },
        "action": {
            "action_recommendation": f"Investigate {label.replace('_', ' ')} cluster and prioritize fix in next sprint.",
            "action_type": "investigation",
            "effort_estimate": "medium_term",
        },
        "method": "deterministic_fallback",
        "agents_executed": AGENT_CHAIN,
    }


# ---------------------------------------------------------------------------
# Anthropic tool_use orchestrator
# ---------------------------------------------------------------------------

def _build_orchestrator_prompt(evidence_text: str, context: dict[str, Any]) -> str:
    source = context.get("source_name", "unknown")
    platform = context.get("platform_name", "unknown")
    language = context.get("resolved_language", "unknown")
    return f"""You are an expert real estate product intelligence analyst.

Analyse the following user feedback from a real estate platform and call each analysis tool in sequence:
1. classify_evidence — classify the feedback type and journey stage
2. extract_pain_point — extract the specific pain point
3. analyse_root_cause — hypothesize the root cause
4. benchmark_competitor — identify any competitor context
5. recommend_action — recommend a product action

Context:
- Source: {source}
- Platform: {platform}
- Language: {language}

User feedback:
\"\"\"{evidence_text[:800]}\"\"\"

Call all 5 tools to complete the analysis."""


def _call_anthropic_agents(evidence_text: str, context: dict[str, Any]) -> dict[str, Any]:
    """Run the multi-agent pipeline via Anthropic tool_use."""
    settings = get_settings()
    client = _anthropic_sdk.Anthropic(api_key=settings.anthropic_api_key)

    messages = [
        {
            "role": "user",
            "content": _build_orchestrator_prompt(evidence_text, context),
        }
    ]

    collected: dict[str, Any] = {}
    agents_executed: list[str] = []
    max_rounds = 8

    for _round in range(max_rounds):
        response = client.messages.create(
            model=settings.agent_orchestrator_model,
            max_tokens=1500,
            tools=AGENT_TOOLS,
            messages=messages,
        )

        # Append assistant response
        messages.append({"role": "assistant", "content": response.content})

        # Process tool calls
        tool_calls = [b for b in response.content if b.type == "tool_use"]
        if not tool_calls:
            break

        tool_results = []
        for tool_use_block in tool_calls:
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input

            # Store the structured output from this agent
            agent_key = {
                "classify_evidence": "classification",
                "extract_pain_point": "pain_point",
                "analyse_root_cause": "root_cause",
                "benchmark_competitor": "competitor",
                "recommend_action": "action",
            }.get(tool_name, tool_name)
            collected[agent_key] = tool_input
            agents_executed.append(tool_name)

            # Return acknowledgement so the model can continue
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": json.dumps({"status": "recorded", "tool": tool_name}),
                }
            )

        messages.append({"role": "user", "content": tool_results})

        if response.stop_reason == "end_turn":
            break

    collected["method"] = "anthropic_tool_use"
    collected["agents_executed"] = agents_executed
    return collected


# ---------------------------------------------------------------------------
# Main service class
# ---------------------------------------------------------------------------

class AgentOrchestratorService:
    """
    Orchestrates 5 specialized analysis agents over a single evidence item.

    Uses Anthropic Claude with tool_use when available; falls back to
    deterministic rule-based logic otherwise.
    """

    @staticmethod
    def is_enabled() -> bool:
        settings = get_settings()
        return (
            _ANTHROPIC_AVAILABLE
            and getattr(settings, "anthropic_api_key", None) is not None
            and getattr(settings, "agent_orchestrator_enabled", False)
        )

    @staticmethod
    def analyse(
        evidence_text: str,
        context: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Run multi-agent analysis on a single evidence text.
        Returns structured output from all 5 agents.
        """
        ctx = context or {}

        # Cache key: hash of text + context
        cache_key_input = f"{evidence_text[:500]}||{json.dumps(ctx, sort_keys=True)}"

        if use_cache:
            cached = _cache.get(cache_key_input)
            if cached is not None:
                cached["_cache_hit"] = True
                return cached

        if AgentOrchestratorService.is_enabled():
            try:
                result = _call_anthropic_agents(evidence_text, ctx)
            except Exception as exc:
                logger.warning("Agent orchestration via Anthropic failed: %s; using fallback", exc)
                result = _deterministic_fallback(evidence_text, ctx)
        else:
            result = _deterministic_fallback(evidence_text, ctx)

        result["_cache_hit"] = False
        if use_cache:
            _cache.set(cache_key_input, result)
        return result

    @staticmethod
    def analyse_batch(
        evidence_items: list[dict[str, Any]],
        max_items: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Run analysis on a batch of evidence items.
        Each item: {"text": str, "context": dict, "evidence_id": int}
        """
        results = []
        for item in evidence_items[:max_items]:
            text = item.get("text", "")
            ctx = item.get("context", {})
            ev_id = item.get("evidence_id")

            try:
                result = AgentOrchestratorService.analyse(text, ctx)
                result["evidence_id"] = ev_id
                results.append(result)
            except Exception as exc:
                logger.error("Agent analysis failed for evidence %s: %s", ev_id, exc)
                results.append(
                    {
                        "evidence_id": ev_id,
                        "method": "error",
                        "error": str(exc),
                        "classification": {},
                        "pain_point": {},
                        "root_cause": {},
                        "competitor": {},
                        "action": {},
                        "agents_executed": [],
                    }
                )
        return results

    @staticmethod
    def get_agent_status() -> dict[str, Any]:
        """Return current capability status of the orchestrator."""
        settings = get_settings()
        return {
            "anthropic_sdk_available": _ANTHROPIC_AVAILABLE,
            "orchestrator_enabled": AgentOrchestratorService.is_enabled(),
            "anthropic_api_key_configured": bool(getattr(settings, "anthropic_api_key", None)),
            "model": getattr(settings, "agent_orchestrator_model", "claude-3-haiku-20240307"),
            "fallback_available": True,
            "agents": [t["name"] for t in AGENT_TOOLS],
            "cache_stats": _cache.stats(),
        }
