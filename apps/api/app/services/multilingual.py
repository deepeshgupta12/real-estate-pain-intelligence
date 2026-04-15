import logging
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.raw_evidence import RawEvidence
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService
from app.services.run_logger import get_run_logger, teardown_run_logger

logger = logging.getLogger(__name__)

# Common Hindi/Hinglish function words that indicate Roman-script Hindi text
HINGLISH_MARKERS = {
    # Copula / auxiliary
    "hai", "hain", "tha", "thi", "the", "hoga", "hogi", "ho",
    # Particles / postpositions
    "ka", "ki", "ke", "mein", "se", "ko", "par", "tak", "wala", "wali", "wale",
    # Negation
    "nahi", "nahi", "mat", "na",
    # Conjunctions
    "aur", "ya", "lekin", "par", "magar", "isliye", "kyunki",
    # Pronouns
    "ye", "yeh", "wo", "woh", "ek", "koi", "kuch", "sab", "hum",
    "main", "mujhe", "mere", "mera", "tera", "tum", "aap", "unhe",
    # Question words
    "kya", "kaise", "kyun", "kab", "kahan", "kaun",
    # Adverbs / intensifiers
    "bahut", "bilkul", "sirf", "bhi", "ab", "toh", "phir", "jab",
    "bohot", "ekdum", "zyada", "thoda",
    # Real estate Hinglish terms
    "ghar", "makaan", "zameen", "plot", "flat", "kiraya", "kirayedar",
    "brokerage", "dallal", "agent",
}

# Hinglish pain-signal words with English equivalents for bridge text enrichment.
# These are injected into the bridge text so the LLM analysis understands the sentiment.
HINGLISH_PAIN_TRANSLATIONS: dict[str, str] = {
    "dhoka": "fraud/betrayal",
    "dhokha": "fraud/betrayal",
    "bekaar": "useless/worthless",
    "bekar": "useless/worthless",
    "bakwas": "rubbish/nonsense",
    "ganda": "bad/dirty",
    "kharab": "bad/damaged",
    "bura": "bad/terrible",
    "pareshan": "troubled/harassed",
    "takleef": "problem/trouble",
    "paisa barbad": "wasted money",
    "paise barbaad": "wasted money",
    "time waste": "wasted time",
    "fraud hai": "it is fraud",
    "problem hai": "there is a problem",
    "bahut bura": "very bad",
    "bahut kharab": "very bad",
    "jhooth": "lie/deception",
    "jhoot": "lie/deception",
    "loot": "robbery/exploitation",
    "loota": "was robbed/exploited",
    "thaga": "was cheated",
    "thaagi": "cheating/deception",
    "galat": "wrong/incorrect",
    "ghalat": "wrong/incorrect",
    "shikayat": "complaint",
    "naraaz": "angry/upset",
    "nafrat": "hate/dislike",
    "mushkil": "difficult/trouble",
    "dikkat": "problem/difficulty",
    "dikkate": "problems/difficulties",
    "nuksaan": "loss/damage",
    "nuksan": "loss/damage",
    "wapas": "return/refund",
    "wapsi": "return/refund",
    "jawab nahi": "no response",
    "reply nahi": "no reply",
    "response nahi": "no response",
    "call nahi": "no call back",
    "support nahi": "no support",
}


def _enrich_hinglish_bridge(text: str) -> str:
    """
    Inject English equivalents of Hinglish pain terms into the text.
    This improves LLM comprehension of Hinglish reviews.
    E.g., "dhoka hua" → "dhoka [fraud/betrayal] hua"
    """
    enriched = text
    for hinglish_term, english_equiv in HINGLISH_PAIN_TRANSLATIONS.items():
        # Case-insensitive replacement that preserves original + adds English gloss
        pattern = re.compile(re.escape(hinglish_term), re.IGNORECASE)
        replacement = f"{hinglish_term} [{english_equiv}]"
        enriched = pattern.sub(replacement, enriched, count=1)
    return enriched


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
        """Detect if text is Hinglish (Roman script with Hindi/Urdu words).

        A text is Hinglish if:
        - It uses Latin script (no Devanagari), AND
        - It contains at least 2 Hindi marker words, OR at least 1 Hinglish pain term.
        The lower threshold (1 pain term) catches short-form Hinglish reviews common
        on Indian app stores (e.g. "app bahut slow hai, fraud hai").
        """
        if not text:
            return False
        text_lower = text.lower()
        words = set(text_lower.split())
        marker_overlap = words & HINGLISH_MARKERS
        if len(marker_overlap) >= 2:
            return True
        # Single strong pain-signal term is enough
        if any(term in text_lower for term in HINGLISH_PAIN_TRANSLATIONS):
            return True
        return False

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
        """
        Build bridge text for the LLM analysis step.

        For English: return as-is.
        For Hinglish (hi-Latn): enrich with English glosses for pain terms so the LLM
          can understand the sentiment without needing multilingual training.
        For Devanagari Hindi / Urdu: prefix with language tag for LLM awareness.
        """
        base_text = evidence.normalized_text or evidence.cleaned_text or evidence.raw_text
        if resolved_language == "en":
            return base_text
        if resolved_language == "hi-Latn":
            # Hinglish: inject English equivalents of known pain terms inline
            enriched = _enrich_hinglish_bridge(base_text)
            return f"[Hinglish review — mixed Hindi/English] {enriched}"
        if resolved_language == "hi":
            return f"[Hindi review] {base_text}"
        if resolved_language == "ur":
            return f"[Urdu review] {base_text}"
        return f"[{resolved_language}] {base_text}"

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
        evidence.multilingual_notes = (
            f"script={script_label}, lang={resolved_language}, family={language_family}"
        )
        return evidence

    @staticmethod
    def process_run(db: Session, run_id: int) -> tuple[ScrapeRun, int, int, int]:
        run_logger, fh = get_run_logger(run_id)
        run_logger.info("=== Multilingual processing started for run %d ===", run_id)
        try:
            run = OrchestratorService.get_run_or_404(db, run_id)

            evidence_items = db.scalars(
                select(RawEvidence)
                .where(RawEvidence.scrape_run_id == run_id)
                .order_by(RawEvidence.id.asc())
            ).all()

            total = len(evidence_items)
            processed_count = 0
            failed_count = 0

            run_logger.info("Processing %d evidence items for multilingual", total)

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
                except Exception as exc:
                    evidence.multilingual_status = "failed"
                    evidence.multilingual_notes = "Multilingual processing failed"
                    failed_count += 1
                    run_logger.warning("Multilingual failed for evidence id=%s: %s", evidence.id, exc)

            db.commit()

            pending_count = total - processed_count - failed_count

            run_logger.info(
                "=== Multilingual complete for run %d — processed=%d, failed=%d, pending=%d ===",
                run_id, processed_count, failed_count, pending_count,
            )

            run = OrchestratorService.update_progress(
                db=db,
                run_id=run_id,
                pipeline_stage="multilingual_completed",
                items_processed=run.items_processed,
                orchestrator_notes=f"Multilingual completed: processed={processed_count}, failed={failed_count}",
            )

            return run, total, processed_count, pending_count + failed_count
        finally:
            teardown_run_logger(run_id, fh)

    @staticmethod
    def list_run_multilingual_summary(db: Session, run_id: int) -> list[RawEvidence]:
        rows = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()
        return list(rows)