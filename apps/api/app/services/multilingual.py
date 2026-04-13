import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService

HINGLISH_MARKERS = {
    "hai", "ka", "ki", "ke", "mein", "nahi", "aur", "kya",
    "ye", "wo", "ek", "se", "ko", "par", "ab", "toh", "bhi",
    "hain", "tha", "thi", "bahut", "koi", "mere", "tera"
}


class MultilingualService:
    @staticmethod
    def _detect_script(text: str) -> str:
        if re.search(r"[\u0900-\u097F]", text):
            return "devanagari"
        if re.search(r"[\u0600-\u06FF]", text):
            return "arabic"
        if re.search(r"[A-Za-z]", text):
            return "latin"
        return "unknown"

    @staticmethod
    def _detect_language_from_text(text: str) -> str | None:
        """Try to detect language from text content using langdetect if available."""
        try:
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 42  # Deterministic
            if text and len(text.strip()) > 20:
                detected = detect(text.strip())
                return detected
        except Exception:
            pass
        return None

    @staticmethod
    def _is_hinglish(text: str) -> bool:
        """Detect if text is Hinglish (Roman script with Hindi words)."""
        if not text:
            return False
        words = set(text.lower().split())
        overlap = words & HINGLISH_MARKERS
        return len(overlap) >= 2

    @staticmethod
    def _resolve_language(evidence: RawEvidence, script_label: str) -> str:
        candidate = evidence.normalized_language or evidence.language
        if candidate and candidate.strip():
            return candidate.strip().lower()

        base_text = evidence.normalized_text or evidence.cleaned_text or evidence.raw_text

        # Try langdetect if available
        if script_label == "latin":
            detected = MultilingualService._detect_language_from_text(base_text)
            if detected:
                return detected

        # Check for Hinglish
        if script_label == "latin" and MultilingualService._is_hinglish(base_text):
            return "hi-Latn"

        if script_label == "devanagari":
            return "hi"
        if script_label == "arabic":
            return "ur"
        if script_label == "latin":
            return "en"
        return "unknown"

    @staticmethod
    def _map_language_family(language_code: str) -> str:
        family_map = {
            "en": "germanic",
            "hi": "indo_aryan",
            "ur": "indo_aryan",
            "mr": "indo_aryan",
            "bn": "indo_aryan",
            "gu": "indo_aryan",
            "pa": "indo_aryan",
        }
        return family_map.get(language_code, "unknown")

    @staticmethod
    def _build_bridge_text(evidence: RawEvidence, resolved_language: str) -> str:
        base_text = evidence.normalized_text or evidence.cleaned_text or evidence.raw_text
        if resolved_language == "en":
            return base_text
        return f"[bridge:{resolved_language}] {base_text}"

    @staticmethod
    def process_evidence_row(evidence: RawEvidence) -> RawEvidence:
        base_text = evidence.normalized_text or evidence.cleaned_text or evidence.raw_text
        script_label = MultilingualService._detect_script(base_text)
        resolved_language = MultilingualService._resolve_language(evidence, script_label)
        language_family = MultilingualService._map_language_family(resolved_language)
        bridge_text = MultilingualService._build_bridge_text(evidence, resolved_language)

        evidence.script_label = script_label
        evidence.resolved_language = resolved_language
        evidence.language_family = language_family
        evidence.bridge_text = bridge_text
        evidence.multilingual_status = "processed"
        evidence.multilingual_notes = "Deterministic multilingual processing completed"
        return evidence

    @staticmethod
    def process_run(db: Session, run_id: int) -> tuple[ScrapeRun, int, int, int]:
        run = OrchestratorService.get_run_or_404(db, run_id)

        evidence_items = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()

        total = len(evidence_items)
        processed_count = 0
        failed_count = 0

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="multilingual_processing",
            orchestrator_notes="Multilingual processing started for run evidence",
        )

        for evidence in evidence_items:
            try:
                MultilingualService.process_evidence_row(evidence)
                processed_count += 1
            except Exception:
                evidence.multilingual_status = "failed"
                evidence.multilingual_notes = "Multilingual processing failed"
                failed_count += 1

        db.commit()

        pending_count = total - processed_count - failed_count

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="multilingual_completed",
            items_processed=run.items_processed,
            orchestrator_notes="Multilingual processing completed for run evidence",
        )

        return run, total, processed_count, pending_count + failed_count

    @staticmethod
    def list_run_multilingual_summary(db: Session, run_id: int) -> list[RawEvidence]:
        rows = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()
        return list(rows)