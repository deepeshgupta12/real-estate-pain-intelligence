import json
from typing import Any

from openai import OpenAI

from app.core.config import get_settings
from app.models.raw_evidence import RawEvidence


class LLMIntelligenceService:
    @staticmethod
    def is_enabled() -> bool:
        settings = get_settings()
        return (
            settings.intelligence_mode == "hybrid_llm"
            and settings.intelligence_enable_llm
            and settings.intelligence_llm_provider == "openai"
            and bool(settings.openai_api_key)
        )

    @staticmethod
    def _build_prompt(
        evidence: RawEvidence,
        baseline_fields: dict[str, str | None],
    ) -> str:
        evidence_text = (
            evidence.bridge_text
            or evidence.normalized_text
            or evidence.cleaned_text
            or evidence.raw_text
            or ""
        ).strip()

        return f"""
You are analyzing a single real-estate user complaint signal.

Your task:
1. Read the evidence carefully.
2. Improve the baseline classification if needed.
3. Return ONLY valid JSON.
4. Do not include markdown, explanation, or extra text.

Allowed journey_stage values:
- discovery
- consideration
- conversion
- post_discovery

Allowed priority_label values:
- high
- medium
- low

Return JSON with exactly these keys:
{{
  "journey_stage": "...",
  "pain_point_label": "...",
  "pain_point_summary": "...",
  "taxonomy_cluster": "...",
  "root_cause_hypothesis": "...",
  "competitor_label": "...",
  "priority_label": "...",
  "action_recommendation": "...",
  "confidence_score": "low|medium|high"
}}

Context:
- source_name: {evidence.source_name}
- platform_name: {evidence.platform_name}
- resolved_language: {evidence.resolved_language or evidence.normalized_language or evidence.language or "unknown"}

Evidence text:
\"\"\"{evidence_text}\"\"\"

Baseline suggestion:
{json.dumps(baseline_fields, ensure_ascii=False)}
""".strip()

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("{") and cleaned.endswith("}"):
            return json.loads(cleaned)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("LLM response did not contain a valid JSON object")

        return json.loads(cleaned[start : end + 1])

    @staticmethod
    def _normalize_text(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_choice(value: Any, allowed: set[str]) -> str | None:
        normalized = LLMIntelligenceService._normalize_text(value)
        if normalized is None:
            return None
        lowered = normalized.lower().strip()
        return lowered if lowered in allowed else None

    @staticmethod
    def generate_hybrid_fields(
        evidence: RawEvidence,
        baseline_fields: dict[str, str | None],
    ) -> tuple[dict[str, str | None], dict[str, Any]]:
        settings = get_settings()
        if not LLMIntelligenceService.is_enabled():
            raise RuntimeError("LLM intelligence is not enabled")

        client = OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.intelligence_llm_timeout_seconds,
            max_retries=settings.intelligence_llm_max_retries,
        )

        prompt = LLMIntelligenceService._build_prompt(
            evidence=evidence,
            baseline_fields=baseline_fields,
        )

        response = client.responses.create(
            model=settings.intelligence_openai_model,
            input=prompt,
        )

        output_text = (response.output_text or "").strip()
        if not output_text:
            raise ValueError("LLM returned an empty response")

        parsed = LLMIntelligenceService._extract_json_object(output_text)

        normalized_fields: dict[str, str | None] = {
            "journey_stage": LLMIntelligenceService._normalize_choice(
                parsed.get("journey_stage"),
                {"discovery", "consideration", "conversion", "post_discovery"},
            ),
            "pain_point_label": LLMIntelligenceService._normalize_text(parsed.get("pain_point_label")),
            "pain_point_summary": LLMIntelligenceService._normalize_text(parsed.get("pain_point_summary")),
            "taxonomy_cluster": LLMIntelligenceService._normalize_text(parsed.get("taxonomy_cluster")),
            "root_cause_hypothesis": LLMIntelligenceService._normalize_text(
                parsed.get("root_cause_hypothesis")
            ),
            "competitor_label": LLMIntelligenceService._normalize_text(parsed.get("competitor_label")),
            "priority_label": LLMIntelligenceService._normalize_choice(
                parsed.get("priority_label"),
                {"high", "medium", "low"},
            ),
            "action_recommendation": LLMIntelligenceService._normalize_text(
                parsed.get("action_recommendation")
            ),
            "confidence_score": LLMIntelligenceService._normalize_choice(
                parsed.get("confidence_score"),
                {"low", "medium", "high"},
            ),
        }

        metadata: dict[str, Any] = {
            "llm_provider": settings.intelligence_llm_provider,
            "llm_model_name": settings.intelligence_openai_model,
            "llm_used": True,
            "llm_raw_output": output_text,
        }

        return normalized_fields, metadata