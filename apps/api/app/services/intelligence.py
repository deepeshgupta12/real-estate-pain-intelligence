import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.final_hardening import FinalHardeningService
from app.services.llm_intelligence import LLMIntelligenceService
from app.services.orchestrator import OrchestratorService
from app.services.run_logger import get_run_logger, teardown_run_logger

logger = logging.getLogger(__name__)


class IntelligenceService:
    @staticmethod
    def _get_analysis_text(evidence: RawEvidence) -> str:
        return (
            evidence.bridge_text
            or evidence.normalized_text
            or evidence.cleaned_text
            or evidence.raw_text
        ).lower()

    @staticmethod
    def _derive_journey_stage(text: str) -> str:
        if any(token in text for token in ["listing", "search", "discover", "filter"]):
            return "discovery"
        if any(token in text for token in ["agent", "contact", "callback", "response"]):
            return "consideration"
        if any(token in text for token in ["booking", "visit", "payment", "loan"]):
            return "conversion"
        return "post_discovery"

    @staticmethod
    def _derive_pain_point(text: str) -> tuple[str, str]:
        if any(token in text for token in ["outdated", "old listing", "purani", "पुरानी"]):
            return "outdated_listing", "User is facing outdated or stale property listing information."
        if any(token in text for token in ["slow", "lag", "loading", "response was slow"]):
            return "slow_experience", "User is experiencing slow page or platform response."
        if any(token in text for token in ["agent", "not reachable", "reply", "जवाब नहीं"]):
            return "agent_unresponsive", "User is not getting timely response from the agent."
        if any(token in text for token in ["fraud", "fake", "spam"]):
            return "trust_issue", "User is showing trust or fraud-related concern."
        return "general_experience_issue", "User is facing a general product experience issue."

    @staticmethod
    def _derive_taxonomy_cluster(pain_point_label: str) -> str:
        cluster_map = {
            "outdated_listing": "inventory_quality",
            "slow_experience": "platform_performance",
            "agent_unresponsive": "lead_management",
            "trust_issue": "trust_and_safety",
            "general_experience_issue": "general_product_experience",
        }
        return cluster_map.get(pain_point_label, "general_product_experience")

    @staticmethod
    def _derive_root_cause(pain_point_label: str) -> str:
        cause_map = {
            "outdated_listing": "Listing refresh or deactivation pipeline may be delayed or inconsistent.",
            "slow_experience": "Frontend rendering, backend response, or API latency may be causing slowness.",
            "agent_unresponsive": "Lead routing, notification, or agent follow-up workflow may be weak.",
            "trust_issue": "Verification, moderation, or trust signaling may be insufficient.",
            "general_experience_issue": "Product experience issue needs deeper triage and user signal clustering.",
        }
        return cause_map.get(
            pain_point_label,
            "Potential product issue requires deeper analysis.",
        )

    @staticmethod
    def _derive_competitor_label(platform_name: str) -> str:
        normalized = platform_name.strip().lower()
        mapping = {
            "square yards": "square_yards",
            "99acres": "99acres",
            "magicbricks": "magicbricks",
            "housing.com": "housing_com",
        }
        return mapping.get(platform_name, normalized.replace(" ", "_").replace(".", "_"))

    @staticmethod
    def _derive_priority(pain_point_label: str) -> str:
        if pain_point_label in {"outdated_listing", "agent_unresponsive", "trust_issue"}:
            return "high"
        if pain_point_label in {"slow_experience"}:
            return "medium"
        return "medium"

    @staticmethod
    def _derive_action(pain_point_label: str) -> str:
        action_map = {
            "outdated_listing": "Strengthen stale listing detection and faster listing expiry/deactivation logic.",
            "slow_experience": "Investigate slow screens/APIs and prioritize performance improvements.",
            "agent_unresponsive": "Improve lead routing, response monitoring, and fallback agent workflows.",
            "trust_issue": "Introduce stronger trust badges, verification signals, and fraud reporting interventions.",
            "general_experience_issue": "Cluster similar complaints and define product fixes based on repeated patterns.",
        }
        return action_map.get(
            pain_point_label,
            "Review repeated evidence signals and convert them into product fixes.",
        )

    @staticmethod
    def _build_deterministic_fields(evidence: RawEvidence) -> dict[str, str]:
        text = IntelligenceService._get_analysis_text(evidence)
        journey_stage = IntelligenceService._derive_journey_stage(text)
        pain_point_label, pain_point_summary = IntelligenceService._derive_pain_point(text)
        taxonomy_cluster = IntelligenceService._derive_taxonomy_cluster(pain_point_label)
        root_cause = IntelligenceService._derive_root_cause(pain_point_label)
        competitor_label = IntelligenceService._derive_competitor_label(evidence.platform_name)
        priority_label = IntelligenceService._derive_priority(pain_point_label)
        action_recommendation = IntelligenceService._derive_action(pain_point_label)

        return {
            "journey_stage": journey_stage,
            "pain_point_label": pain_point_label,
            "pain_point_summary": pain_point_summary,
            "taxonomy_cluster": taxonomy_cluster,
            "root_cause_hypothesis": root_cause,
            "competitor_label": competitor_label,
            "priority_label": priority_label,
            "action_recommendation": action_recommendation,
            "confidence_score": "medium",
        }

    @staticmethod
    def _merge_hybrid_fields(
        baseline_fields: dict[str, str | None],
        llm_fields: dict[str, str | None],
    ) -> dict[str, str | None]:
        merged: dict[str, str | None] = {}
        for key, baseline_value in baseline_fields.items():
            llm_value = llm_fields.get(key)
            merged[key] = llm_value if llm_value is not None else baseline_value
        return merged

    @staticmethod
    def _build_metadata(
        evidence: RawEvidence,
        baseline_fields: dict[str, str | None],
        final_fields: dict[str, str | None],
        analysis_mode: str,
        llm_attempted: bool,
        llm_used: bool,
        llm_metadata: dict[str, Any] | None = None,
        llm_error: str | None = None,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "source_name": evidence.source_name,
            "platform_name": evidence.platform_name,
            "resolved_language": evidence.resolved_language,
            "analysis_mode": analysis_mode,
            "llm_attempted": llm_attempted,
            "llm_used": llm_used,
            "baseline_snapshot": baseline_fields,
            "final_snapshot": final_fields,
        }

        if llm_metadata:
            metadata.update(llm_metadata)

        if llm_error:
            metadata["llm_error"] = llm_error

        return metadata

    @staticmethod
    def process_run(db: Session, run_id: int) -> tuple[ScrapeRun, int, int, int, int, int]:
        run_logger, fh = get_run_logger(run_id)
        run_logger.info("=== Intelligence processing started for run %d ===", run_id)
        try:
            run = FinalHardeningService.ensure_run_not_failed(db, run_id)
            FinalHardeningService.ensure_evidence_exists(db, run_id)

            evidence_items = db.scalars(
                select(RawEvidence)
                .where(RawEvidence.scrape_run_id == run_id)
                .order_by(RawEvidence.id.asc())
            ).all()

            db.execute(delete(AgentInsight).where(AgentInsight.scrape_run_id == run_id))
            db.commit()

            total = len(evidence_items)
            generated_count = 0
            llm_generated_count = 0
            deterministic_generated_count = 0
            failed_count = 0

            llm_enabled = LLMIntelligenceService.is_enabled()
            run_logger.info(
                "Processing %d evidence items — LLM enabled=%s", total, llm_enabled
            )

            OrchestratorService.update_progress(
                db=db,
                run_id=run_id,
                pipeline_stage="intelligence_processing",
                orchestrator_notes="Hybrid intelligence processing started",
            )

            for evidence in evidence_items:
                try:
                    baseline_fields = IntelligenceService._build_deterministic_fields(evidence)
                    final_fields = dict(baseline_fields)

                    analysis_mode = "deterministic_only"
                    llm_attempted = False
                    llm_used = False
                    llm_metadata: dict[str, Any] | None = None
                    llm_error: str | None = None

                    if llm_enabled:
                        llm_attempted = True
                        try:
                            llm_fields, llm_metadata = LLMIntelligenceService.generate_hybrid_fields(
                                evidence=evidence,
                                baseline_fields=baseline_fields,
                            )
                            final_fields = IntelligenceService._merge_hybrid_fields(
                                baseline_fields=baseline_fields,
                                llm_fields=llm_fields,
                            )
                            analysis_mode = "llm_assisted"
                            llm_used = True
                            llm_generated_count += 1
                        except Exception as exc:
                            analysis_mode = "deterministic_fallback"
                            llm_used = False
                            llm_error = str(exc)
                            run_logger.warning(
                                "LLM failed for evidence id=%s, falling back to deterministic: %s",
                                evidence.id, exc,
                            )
                            deterministic_generated_count += 1
                    else:
                        deterministic_generated_count += 1

                    run_logger.debug(
                        "Evidence id=%s → pain=%s stage=%s mode=%s",
                        evidence.id,
                        final_fields.get("pain_point_label"),
                        final_fields.get("journey_stage"),
                        analysis_mode,
                    )

                    insight = AgentInsight(
                        scrape_run_id=run_id,
                        raw_evidence_id=evidence.id,
                        journey_stage=final_fields["journey_stage"],
                        pain_point_label=final_fields["pain_point_label"],
                        pain_point_summary=final_fields["pain_point_summary"],
                        taxonomy_cluster=final_fields["taxonomy_cluster"],
                        root_cause_hypothesis=final_fields["root_cause_hypothesis"],
                        competitor_label=final_fields["competitor_label"],
                        priority_label=final_fields["priority_label"],
                        action_recommendation=final_fields["action_recommendation"],
                        confidence_score=final_fields["confidence_score"],
                        insight_status="generated",
                        metadata_json=IntelligenceService._build_metadata(
                            evidence=evidence,
                            baseline_fields=baseline_fields,
                            final_fields=final_fields,
                            analysis_mode=analysis_mode,
                            llm_attempted=llm_attempted,
                            llm_used=llm_used,
                            llm_metadata=llm_metadata,
                            llm_error=llm_error,
                        ),
                    )
                    db.add(insight)
                    generated_count += 1
                except Exception as exc:
                    failed_count += 1
                    run_logger.warning("Intelligence failed for evidence id=%s: %s", evidence.id, exc)

            db.commit()

            run_logger.info(
                "=== Intelligence complete for run %d — generated=%d (llm=%d, deterministic=%d), failed=%d ===",
                run_id, generated_count, llm_generated_count, deterministic_generated_count, failed_count,
            )

            run = OrchestratorService.update_progress(
                db=db,
                run_id=run_id,
                pipeline_stage="intelligence_completed",
                items_processed=run.items_processed,
                orchestrator_notes=(
                    f"Intelligence completed: generated={generated_count} "
                    f"(llm={llm_generated_count}, deterministic={deterministic_generated_count}), "
                    f"failed={failed_count}"
                ),
            )

            return (
                run,
                total,
                generated_count,
                llm_generated_count,
                deterministic_generated_count,
                failed_count,
            )
        finally:
            teardown_run_logger(run_id, fh)

    @staticmethod
    def list_run_insights(db: Session, run_id: int) -> list[AgentInsight]:
        rows = db.scalars(
            select(AgentInsight)
            .where(AgentInsight.scrape_run_id == run_id)
            .order_by(AgentInsight.id.asc())
        ).all()
        return list(rows)