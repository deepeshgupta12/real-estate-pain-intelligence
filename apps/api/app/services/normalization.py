import hashlib
import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService
from app.services.run_logger import get_run_logger, teardown_run_logger

logger = logging.getLogger(__name__)


class NormalizationService:
    @staticmethod
    def _normalize_text(text: str) -> str:
        # Preserve emoji: only collapse repeated punctuation, not all punctuation
        # Collapse 3+ repeated punct chars to 1
        text = re.sub(r'([!?.]){2,}', r'\1', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        return text.strip()

    @staticmethod
    def _detect_language(raw_language: str | None) -> str:
        if raw_language and raw_language.strip():
            return raw_language.strip().lower()
        return "en"

    @staticmethod
    def _build_hash(normalized_text: str) -> str:
        return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()

    @staticmethod
    def normalize_evidence_row(evidence: RawEvidence) -> RawEvidence:
        base_text = evidence.cleaned_text or evidence.raw_text
        normalized_text = NormalizationService._normalize_text(base_text)
        normalized_language = NormalizationService._detect_language(evidence.language)

        evidence.cleaned_text = base_text.strip()
        evidence.normalized_text = normalized_text
        evidence.normalized_language = normalized_language
        evidence.normalization_hash = NormalizationService._build_hash(normalized_text)
        evidence.normalization_status = "normalized"
        return evidence

    @staticmethod
    def normalize_run(db: Session, run_id: int) -> tuple[ScrapeRun, int, int, int]:
        run_logger, fh = get_run_logger(run_id)
        run_logger.info("=== Normalization started for run %d ===", run_id)
        try:
            run = OrchestratorService.get_run_or_404(db, run_id)

            evidence_items = db.scalars(
                select(RawEvidence)
                .where(RawEvidence.scrape_run_id == run_id)
                .order_by(RawEvidence.id.asc())
            ).all()

            total = len(evidence_items)
            normalized_count = 0
            failed_count = 0

            run_logger.info("Normalizing %d evidence items for run %d", total, run_id)

            OrchestratorService.update_progress(
                db=db,
                run_id=run_id,
                pipeline_stage="normalization",
                orchestrator_notes="Normalization started for run evidence",
            )

            for evidence in evidence_items:
                try:
                    NormalizationService.normalize_evidence_row(evidence)
                    normalized_count += 1
                except Exception as exc:
                    evidence.normalization_status = "failed"
                    failed_count += 1
                    run_logger.warning("Normalization failed for evidence id=%s: %s", evidence.id, exc)

            db.commit()

            pending_count = total - normalized_count - failed_count

            run_logger.info(
                "=== Normalization complete for run %d — normalized=%d, failed=%d, pending=%d ===",
                run_id, normalized_count, failed_count, pending_count,
            )

            run = OrchestratorService.update_progress(
                db=db,
                run_id=run_id,
                pipeline_stage="normalization_completed",
                items_processed=run.items_processed,
                orchestrator_notes=f"Normalization completed: normalized={normalized_count}, failed={failed_count}",
            )

            return run, total, normalized_count, pending_count + failed_count
        finally:
            teardown_run_logger(run_id, fh)

    @staticmethod
    def list_run_normalization_summary(db: Session, run_id: int) -> list[RawEvidence]:
        rows = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()
        return list(rows)