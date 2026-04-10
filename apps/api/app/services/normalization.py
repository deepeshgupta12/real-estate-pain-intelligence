import hashlib
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService


class NormalizationService:
    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = text.replace("\n", " ")
        return text

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
        run = OrchestratorService.get_run_or_404(db, run_id)

        evidence_items = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()

        total = len(evidence_items)
        normalized_count = 0
        failed_count = 0

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
            except Exception:
                evidence.normalization_status = "failed"
                failed_count += 1

        db.commit()

        pending_count = total - normalized_count - failed_count

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="normalization_completed",
            items_processed=run.items_processed,
            orchestrator_notes="Normalization completed for run evidence",
        )

        return run, total, normalized_count, pending_count + failed_count

    @staticmethod
    def list_run_normalization_summary(db: Session, run_id: int) -> list[RawEvidence]:
        rows = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()
        return list(rows)