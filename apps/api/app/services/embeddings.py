"""
Embedding service with two backends:
1. SentenceTransformers (production): real semantic embeddings via paraphrase-multilingual-MiniLM-L12-v2
   - Supports English + Hindi/Hinglish
   - ~117MB model, runs on CPU
   - Cached after first load
2. DeterministicHash (fallback): the existing hash-bucketing approach
   - No external dependencies
   - Used when sentence-transformers is not installed or model fails to load
"""
import hashlib
import logging
import math
import re
from typing import Sequence

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Domain-specific semantic term groups for Indian real estate
# Terms in the same group will have similar embedding directions
SEMANTIC_GROUPS: list[tuple[str, ...]] = [
    # Pain: listing quality
    ("stale", "outdated", "old", "wrong", "incorrect", "inaccurate", "listing", "inventory", "fake"),
    # Pain: response/callback issues
    ("callback", "response", "reply", "contacted", "agent", "broker", "followup", "ignored"),
    # Pain: pricing/hidden costs
    ("price", "cost", "expensive", "hidden", "charges", "fees", "brokerage", "overpriced"),
    # Pain: platform UX
    ("filter", "search", "ui", "app", "website", "slow", "crash", "load", "navigation", "interface"),
    # Pain: trust/fraud
    ("fraud", "fake", "scam", "cheat", "mislead", "trust", "verified", "genuine"),
    # Positive signals
    ("good", "great", "excellent", "satisfied", "happy", "recommend", "useful", "helpful"),
    # Brands: competitors
    ("squareyards", "square", "yards", "99acres", "magicbricks", "housing", "nobroker", "commonfloor"),
    # Property types
    ("flat", "apartment", "villa", "plot", "commercial", "residential", "bhk", "studio"),
    # Location terms India
    ("mumbai", "delhi", "bangalore", "pune", "hyderabad", "chennai", "kolkata", "gurgaon", "noida"),
    # Transaction stages
    ("buy", "rent", "lease", "sell", "invest", "purchase", "booking", "registration"),
]

TERM_GROUP: dict[str, int] = {
    term: idx for idx, group in enumerate(SEMANTIC_GROUPS) for term in group
}

# ── Lazy model loader ────────────────────────────────────────────────────────
_sentence_model = None
_sentence_model_loaded = False


def _load_sentence_model():
    global _sentence_model, _sentence_model_loaded
    if _sentence_model_loaded:
        return _sentence_model

    _sentence_model_loaded = True
    try:
        from sentence_transformers import SentenceTransformer
        model_name = "paraphrase-multilingual-MiniLM-L12-v2"
        logger.info(f"Loading sentence-transformers model: {model_name}")
        _sentence_model = SentenceTransformer(model_name)
        logger.info("sentence-transformers model loaded successfully")
        return _sentence_model
    except ImportError:
        logger.info("sentence-transformers not installed — using deterministic hash embeddings")
        return None
    except Exception as exc:
        logger.warning(f"Failed to load sentence-transformers model: {exc} — using hash fallback")
        return None


class EmbeddingService:
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s]+", " ", text.lower())
        return [token for token in cleaned.split() if len(token) > 1]

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    @staticmethod
    def _hash_embed(text: str) -> list[float]:
        """Fallback: 128-dim domain-aware hash embedding."""
        settings = get_settings()
        dimensions = settings.embedding_dimensions
        vector = [0.0] * dimensions
        tokens = EmbeddingService._tokenize(text)
        if not tokens:
            return vector

        total_tokens = len(tokens)
        for position, token in enumerate(tokens):
            position_weight = 1.5 if position < max(1, total_tokens // 5) else 1.0
            group_idx = TERM_GROUP.get(token)
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            magnitude = 1.0 + ((digest[5] % 7) / 10.0)
            vector[bucket] += sign * magnitude * position_weight
            if group_idx is not None:
                anchor_bucket = (group_idx * 7 + 13) % dimensions
                vector[anchor_bucket] += sign * magnitude * 2.0 * position_weight

        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            digest = hashlib.sha256(bigram.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign * 0.5

        return EmbeddingService._normalize(vector)

    @staticmethod
    def embed_text(text: str) -> list[float]:
        """Generate embedding for text. Uses sentence-transformers if available."""
        settings = get_settings()
        model = _load_sentence_model()

        if model is not None:
            try:
                embedding = model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as exc:
                logger.warning(f"sentence-transformers encode failed: {exc} — using hash fallback")

        return EmbeddingService._hash_embed(text)

    @staticmethod
    def embed_query(query: str) -> list[float]:
        return EmbeddingService.embed_text(query)

    @staticmethod
    def cosine_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
        if not vector_a or not vector_b or len(vector_a) != len(vector_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = math.sqrt(sum(a * a for a in vector_a))
        norm_b = math.sqrt(sum(b * b for b in vector_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @staticmethod
    def get_embedding_info() -> dict:
        """Return info about which embedding backend is active."""
        model = _load_sentence_model()
        if model is not None:
            return {
                "backend": "sentence_transformers",
                "model": "paraphrase-multilingual-MiniLM-L12-v2",
                "dimensions": 384,
                "multilingual": True,
            }
        return {
            "backend": "deterministic_hash",
            "model": "hash-embedding-domain-v2",
            "dimensions": 128,
            "multilingual": False,
        }