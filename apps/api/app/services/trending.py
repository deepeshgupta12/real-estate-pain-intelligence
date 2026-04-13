"""
Pain point trending service.
After intelligence generation, fingerprints each pain point and updates the global trend table.
"""
import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.pain_point_fingerprint import PainPointFingerprint

logger = logging.getLogger(__name__)

PRIORITY_SCORES = {"high": 3.0, "medium": 2.0, "low": 1.0}


def _build_fingerprint_key(pain_point_label: str, taxonomy_cluster: str | None) -> str:
    """Build a stable fingerprint key for a pain point concept."""
    normalized = f"{(pain_point_label or '').lower().strip()}:{(taxonomy_cluster or '').lower().strip()}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def _calculate_trend(ppf: PainPointFingerprint) -> str:
    """Determine trend direction from weekly counts."""
    recent = ppf.count_week_0
    prior = ppf.count_week_1 + ppf.count_week_2
    if prior == 0:
        return "stable"
    rate = recent / (prior / 2)
    if rate > 1.5:
        return "rising"
    if rate < 0.5:
        return "declining"
    return "stable"


class TrendingService:
    @staticmethod
    def update_fingerprints_for_run(db: Session, run_id: int) -> dict:
        """
        After intelligence generation for a run, update or create pain point fingerprints.
        Returns summary of changes.
        """
        insights = (
            db.query(AgentInsight)
            .filter(AgentInsight.scrape_run_id == run_id)
            .all()
        )

        created = 0
        updated = 0
        now = datetime.now(timezone.utc)
        current_week_start = now - timedelta(days=now.weekday())

        for insight in insights:
            if not insight.pain_point_label:
                continue

            key = _build_fingerprint_key(insight.pain_point_label, insight.taxonomy_cluster)
            priority_score = PRIORITY_SCORES.get(insight.priority_label or "low", 1.0)

            existing = db.query(PainPointFingerprint).filter(
                PainPointFingerprint.fingerprint_key == key
            ).first()

            if existing is None:
                ppf = PainPointFingerprint(
                    fingerprint_key=key,
                    pain_point_label=insight.pain_point_label,
                    taxonomy_cluster=insight.taxonomy_cluster,
                    competitor_label=insight.competitor_label,
                    recurrence_count=1,
                    first_seen_at=now,
                    last_seen_at=now,
                    count_week_0=1,
                    high_priority_count=1 if insight.priority_label == "high" else 0,
                    avg_priority_score=priority_score,
                    example_text=(insight.pain_point_summary or "")[:500],
                )
                ppf.trend_direction = "stable"
                db.add(ppf)
                created += 1
            else:
                existing.recurrence_count += 1
                existing.last_seen_at = now
                existing.count_week_0 += 1
                if insight.priority_label == "high":
                    existing.high_priority_count += 1
                # Update rolling average
                n = existing.recurrence_count
                existing.avg_priority_score = (
                    (existing.avg_priority_score * (n - 1) + priority_score) / n
                )
                existing.trend_direction = _calculate_trend(existing)
                if not existing.example_text and insight.pain_point_summary:
                    existing.example_text = insight.pain_point_summary[:500]
                updated += 1

        db.commit()
        logger.info(f"Trending: run {run_id} — {created} created, {updated} updated fingerprints")
        return {"run_id": run_id, "fingerprints_created": created, "fingerprints_updated": updated}

    @staticmethod
    def get_top_trending(db: Session, limit: int = 20, cluster: str | None = None) -> list[dict]:
        """Get the top trending pain points globally."""
        query = db.query(PainPointFingerprint).order_by(
            PainPointFingerprint.recurrence_count.desc()
        )
        if cluster:
            query = query.filter(PainPointFingerprint.taxonomy_cluster == cluster)

        results = query.limit(limit).all()
        return [
            {
                "pain_point": r.pain_point_label,
                "taxonomy": r.taxonomy_cluster,
                "competitor": r.competitor_label,
                "occurrences": r.recurrence_count,
                "trend": r.trend_direction,
                "first_seen": r.first_seen_at.isoformat() if r.first_seen_at else None,
                "last_seen": r.last_seen_at.isoformat() if r.last_seen_at else None,
                "high_priority_count": r.high_priority_count,
                "avg_priority_score": round(r.avg_priority_score, 2),
                "example": r.example_text,
            }
            for r in results
        ]

    @staticmethod
    def rotate_weekly_counts(db: Session) -> None:
        """
        Rotate weekly count buckets. Call this weekly via a scheduled job.
        count_week_3 gets dropped, everything shifts right, week_0 resets.
        """
        db.execute(
            "UPDATE pain_point_fingerprints SET "
            "count_week_3 = count_week_2, "
            "count_week_2 = count_week_1, "
            "count_week_1 = count_week_0, "
            "count_week_0 = 0"
        )
        db.commit()
