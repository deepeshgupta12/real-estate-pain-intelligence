from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService


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
    def process_run(db: Session, run_id: int) -> tuple[ScrapeRun, int, int, int]:
        run = OrchestratorService.get_run_or_404(db, run_id)

        evidence_items = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()

        db.execute(delete(AgentInsight).where(AgentInsight.scrape_run_id == run_id))
        db.commit()

        total = len(evidence_items)
        generated_count = 0
        failed_count = 0

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="intelligence_processing",
            orchestrator_notes="Multi-agent intelligence processing started",
        )

        for evidence in evidence_items:
            try:
                text = IntelligenceService._get_analysis_text(evidence)
                journey_stage = IntelligenceService._derive_journey_stage(text)
                pain_point_label, pain_point_summary = IntelligenceService._derive_pain_point(text)
                taxonomy_cluster = IntelligenceService._derive_taxonomy_cluster(pain_point_label)
                root_cause = IntelligenceService._derive_root_cause(pain_point_label)
                competitor_label = IntelligenceService._derive_competitor_label(evidence.platform_name)
                priority_label = IntelligenceService._derive_priority(pain_point_label)
                action_recommendation = IntelligenceService._derive_action(pain_point_label)

                insight = AgentInsight(
                    scrape_run_id=run_id,
                    raw_evidence_id=evidence.id,
                    journey_stage=journey_stage,
                    pain_point_label=pain_point_label,
                    pain_point_summary=pain_point_summary,
                    taxonomy_cluster=taxonomy_cluster,
                    root_cause_hypothesis=root_cause,
                    competitor_label=competitor_label,
                    priority_label=priority_label,
                    action_recommendation=action_recommendation,
                    confidence_score="medium",
                    insight_status="generated",
                    metadata_json={
                        "source_name": evidence.source_name,
                        "platform_name": evidence.platform_name,
                        "resolved_language": evidence.resolved_language,
                    },
                )
                db.add(insight)
                generated_count += 1
            except Exception:
                failed_count += 1

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="intelligence_completed",
            items_processed=run.items_processed,
            orchestrator_notes="Multi-agent intelligence processing completed",
        )

        return run, total, generated_count, failed_count

    @staticmethod
    def list_run_insights(db: Session, run_id: int) -> list[AgentInsight]:
        rows = db.scalars(
            select(AgentInsight)
            .where(AgentInsight.scrape_run_id == run_id)
            .order_by(AgentInsight.id.asc())
        ).all()
        return list(rows)