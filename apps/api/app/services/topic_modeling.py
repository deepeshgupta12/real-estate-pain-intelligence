"""
Topic modeling service — discovers latent pain-point clusters using
NMF/LDA (always-available via scikit-learn) with optional BERTopic
integration when sentence-transformers + hdbscan are installed.
"""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Any

from sqlalchemy.orm import Session

from app.models.scrape_run import ScrapeRun
from app.models.raw_evidence import RawEvidence

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional heavy imports — graceful fallback to TF-IDF + NMF if not present
# ---------------------------------------------------------------------------
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import NMF, LatentDirichletAllocation

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not installed; topic modeling will return stub output")

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np

    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

try:
    import hdbscan as hdbscan_module

    _HDBSCAN_AVAILABLE = True
except ImportError:
    _HDBSCAN_AVAILABLE = False


# ---------------------------------------------------------------------------
# Singleton model cache
# ---------------------------------------------------------------------------
_tfidf_vectorizer: Any | None = None
_nmf_model: Any | None = None
_lda_model: Any | None = None
_st_model: Any | None = None

_EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

REAL_ESTATE_PAIN_SEEDS: list[dict[str, Any]] = [
    {
        "id": "inventory_quality",
        "label": "Inventory & Listing Quality",
        "keywords": ["outdated", "stale", "wrong", "inaccurate", "fake listing", "old", "purani"],
        "description": "Issues related to listing accuracy, freshness, and quality.",
    },
    {
        "id": "platform_performance",
        "label": "Platform Performance & Reliability",
        "keywords": ["slow", "lag", "loading", "crash", "app down", "timeout", "error"],
        "description": "Issues related to app speed, stability, and uptime.",
    },
    {
        "id": "lead_management",
        "label": "Lead Management & Agent Responsiveness",
        "keywords": ["agent", "callback", "no reply", "unresponsive", "contact", "enquiry"],
        "description": "Issues with agent responsiveness, lead routing, and follow-up.",
    },
    {
        "id": "trust_and_safety",
        "label": "Trust, Safety & Fraud",
        "keywords": ["fraud", "fake", "scam", "spam", "cheated", "misleading"],
        "description": "Issues around fraudulent listings, scams, and trust signals.",
    },
    {
        "id": "pricing_transparency",
        "label": "Pricing & Transparency",
        "keywords": ["pricing", "hidden", "extra charge", "overpriced", "negotiation", "fees"],
        "description": "Issues around pricing clarity, hidden charges, and transparency.",
    },
    {
        "id": "search_discovery",
        "label": "Search & Discovery",
        "keywords": ["search", "filter", "can't find", "results", "location", "map"],
        "description": "Issues with search quality, filters, and property discovery.",
    },
    {
        "id": "transaction_process",
        "label": "Transaction & Documentation Process",
        "keywords": ["payment", "loan", "verification", "document", "emi", "agreement"],
        "description": "Issues in payment, documentation, and closing the deal.",
    },
    {
        "id": "ux_design",
        "label": "UX & Product Design",
        "keywords": ["confusing", "hard to use", "navigate", "interface", "ux", "design"],
        "description": "Issues with the interface, usability, and navigation.",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_text_for_evidence(ev: RawEvidence) -> str:
    return (
        ev.bridge_text
        or ev.normalized_text
        or ev.cleaned_text
        or ev.raw_text
        or ""
    ).strip()


def _seed_cluster_score(text: str, keywords: list[str]) -> float:
    """Fast keyword overlap score in [0, 1]."""
    text_l = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_l)
    return hits / max(len(keywords), 1)


def _assign_seed_cluster(text: str) -> tuple[str, float]:
    """Assign the best seed cluster using keyword overlap."""
    best_id = "general_pain"
    best_score = 0.0
    for seed in REAL_ESTATE_PAIN_SEEDS:
        score = _seed_cluster_score(text, seed["keywords"])
        if score > best_score:
            best_score = score
            best_id = seed["id"]
    return best_id, best_score


# ---------------------------------------------------------------------------
# NMF / LDA topic extraction
# ---------------------------------------------------------------------------

def _run_nmf(texts: list[str], n_topics: int = 8) -> list[dict[str, Any]]:
    """Run NMF and return topic summaries."""
    if not _SKLEARN_AVAILABLE:
        return []
    global _tfidf_vectorizer, _nmf_model

    try:
        vectorizer = TfidfVectorizer(
            max_df=0.85,
            min_df=2,
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
        )
        tfidf = vectorizer.fit_transform(texts)

        n_topics = min(n_topics, max(2, len(texts) // 3))
        nmf = NMF(n_components=n_topics, random_state=42, max_iter=300)
        W = nmf.fit_transform(tfidf)

        feature_names = vectorizer.get_feature_names_out()
        results = []
        for topic_idx in range(n_topics):
            top_idx = nmf.components_[topic_idx].argsort()[:-11:-1]
            top_words = [feature_names[i] for i in top_idx]
            doc_assignments = (W[:, topic_idx] > 0.1).sum()
            results.append(
                {
                    "topic_id": f"nmf_topic_{topic_idx}",
                    "method": "nmf",
                    "top_keywords": top_words,
                    "document_count": int(doc_assignments),
                    "weight": float(nmf.components_[topic_idx].max()),
                }
            )
        return results
    except Exception as exc:
        logger.warning("NMF topic extraction failed: %s", exc)
        return []


def _run_lda(texts: list[str], n_topics: int = 8) -> list[dict[str, Any]]:
    """Run LDA and return topic summaries."""
    if not _SKLEARN_AVAILABLE:
        return []

    try:
        from sklearn.feature_extraction.text import CountVectorizer

        vectorizer = CountVectorizer(
            max_df=0.85,
            min_df=2,
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
        )
        counts = vectorizer.fit_transform(texts)
        n_topics = min(n_topics, max(2, len(texts) // 3))
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=20,
            learning_method="online",
        )
        doc_topic_matrix = lda.fit_transform(counts)

        feature_names = vectorizer.get_feature_names_out()
        results = []
        for topic_idx in range(n_topics):
            top_idx = lda.components_[topic_idx].argsort()[:-11:-1]
            top_words = [feature_names[i] for i in top_idx]
            doc_assignments = (doc_topic_matrix.argmax(axis=1) == topic_idx).sum()
            results.append(
                {
                    "topic_id": f"lda_topic_{topic_idx}",
                    "method": "lda",
                    "top_keywords": top_words,
                    "document_count": int(doc_assignments),
                    "weight": float(lda.components_[topic_idx].max()),
                }
            )
        return results
    except Exception as exc:
        logger.warning("LDA topic extraction failed: %s", exc)
        return []


def _run_hdbscan_clustering(texts: list[str]) -> list[dict[str, Any]]:
    """Run embedding-based HDBSCAN clustering (BERTopic-style) if deps available."""
    if not (_ST_AVAILABLE and _HDBSCAN_AVAILABLE):
        return []

    try:
        import numpy as np

        global _st_model
        if _st_model is None:
            _st_model = SentenceTransformer(_EMBEDDING_MODEL_NAME)

        embeddings = _st_model.encode(texts, normalize_embeddings=True)
        clusterer = hdbscan_module.HDBSCAN(
            min_cluster_size=max(3, len(texts) // 10),
            metric="euclidean",
            cluster_selection_method="eom",
        )
        labels = clusterer.fit_predict(embeddings)

        unique_labels = set(labels) - {-1}
        results = []
        for label in sorted(unique_labels):
            indices = [i for i, l in enumerate(labels) if l == label]
            cluster_texts = [texts[i] for i in indices]

            # Extract representative keywords using TF-IDF on cluster docs
            if _SKLEARN_AVAILABLE and len(cluster_texts) >= 2:
                try:
                    vec = TfidfVectorizer(max_features=10, stop_words="english")
                    vec.fit(cluster_texts)
                    top_words = vec.get_feature_names_out().tolist()
                except Exception:
                    top_words = []
            else:
                top_words = []

            results.append(
                {
                    "topic_id": f"hdbscan_cluster_{label}",
                    "method": "hdbscan",
                    "top_keywords": top_words,
                    "document_count": len(indices),
                    "weight": float(clusterer.probabilities_[indices].mean()) if hasattr(clusterer, "probabilities_") else 0.5,
                }
            )
        return results
    except Exception as exc:
        logger.warning("HDBSCAN clustering failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------

class TopicModelingService:
    """
    Discovers latent pain-point topics from run evidence using:
    1. Seed-keyword cluster assignment (always available, instant)
    2. NMF topic extraction (requires scikit-learn)
    3. LDA topic extraction (requires scikit-learn)
    4. HDBSCAN semantic clustering (requires sentence-transformers + hdbscan)
    """

    @staticmethod
    def run_topic_modeling(db: Session, run_id: int) -> dict[str, Any]:
        """
        Run full topic modeling pipeline for a scrape run.
        Returns structured topic analysis results.
        """
        run = db.get(ScrapeRun, run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        from sqlalchemy import select

        evidences = db.execute(
            select(RawEvidence).where(RawEvidence.run_id == run_id)
        ).scalars().all()

        if not evidences:
            return {
                "run_id": run_id,
                "evidence_count": 0,
                "seed_clusters": [],
                "ml_topics": [],
                "method_used": "none",
                "status": "no_evidence",
            }

        texts = [_get_text_for_evidence(ev) for ev in evidences]
        texts = [t for t in texts if len(t.strip()) > 10]

        if not texts:
            return {
                "run_id": run_id,
                "evidence_count": len(evidences),
                "seed_clusters": [],
                "ml_topics": [],
                "method_used": "none",
                "status": "insufficient_text",
            }

        # 1. Seed-based cluster assignment
        seed_cluster_counts: dict[str, int] = {}
        seed_cluster_scores: dict[str, float] = {}
        for text in texts:
            cluster_id, score = _assign_seed_cluster(text)
            seed_cluster_counts[cluster_id] = seed_cluster_counts.get(cluster_id, 0) + 1
            seed_cluster_scores[cluster_id] = max(seed_cluster_scores.get(cluster_id, 0.0), score)

        seed_clusters = []
        for seed in REAL_ESTATE_PAIN_SEEDS:
            sid = seed["id"]
            count = seed_cluster_counts.get(sid, 0)
            seed_clusters.append(
                {
                    "cluster_id": sid,
                    "label": seed["label"],
                    "description": seed["description"],
                    "keywords": seed["keywords"],
                    "document_count": count,
                    "coverage_pct": round(count / len(texts) * 100, 1),
                    "max_score": round(seed_cluster_scores.get(sid, 0.0), 3),
                }
            )
        seed_clusters.sort(key=lambda x: x["document_count"], reverse=True)

        # 2. ML-based topic extraction
        ml_topics: list[dict[str, Any]] = []
        method_used = "seed_only"

        if len(texts) >= 5:
            # Try HDBSCAN first (richest), fall back to NMF, then LDA
            if _ST_AVAILABLE and _HDBSCAN_AVAILABLE:
                hdbscan_topics = _run_hdbscan_clustering(texts)
                if hdbscan_topics:
                    ml_topics = hdbscan_topics
                    method_used = "hdbscan_semantic"

            if not ml_topics and _SKLEARN_AVAILABLE:
                nmf_topics = _run_nmf(texts)
                if nmf_topics:
                    ml_topics = nmf_topics
                    method_used = "nmf"
                else:
                    lda_topics = _run_lda(texts)
                    if lda_topics:
                        ml_topics = lda_topics
                        method_used = "lda"

        # 3. Cross-reference ML topics with seed clusters
        enriched_topics = []
        for topic in ml_topics:
            top_kw = topic.get("top_keywords", [])
            best_seed = "general_pain"
            best_overlap = 0
            for seed in REAL_ESTATE_PAIN_SEEDS:
                overlap = sum(1 for kw in top_kw if any(s in kw for s in seed["keywords"]))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_seed = seed["id"]
            enriched_topics.append(
                {
                    **topic,
                    "mapped_seed_cluster": best_seed,
                    "seed_overlap_score": best_overlap,
                }
            )

        # 4. Compute topic diversity score (Shannon entropy)
        total = len(texts)
        cluster_sizes = [c["document_count"] for c in seed_clusters if c["document_count"] > 0]
        entropy = 0.0
        if cluster_sizes:
            for size in cluster_sizes:
                p = size / total
                if p > 0:
                    entropy -= p * math.log2(p)

        return {
            "run_id": run_id,
            "evidence_count": len(evidences),
            "analyzed_count": len(texts),
            "seed_clusters": seed_clusters,
            "ml_topics": enriched_topics,
            "method_used": method_used,
            "topic_diversity_entropy": round(entropy, 3),
            "top_cluster": seed_clusters[0]["cluster_id"] if seed_clusters else None,
            "status": "completed",
            "capabilities": {
                "sklearn_available": _SKLEARN_AVAILABLE,
                "sentence_transformers_available": _ST_AVAILABLE,
                "hdbscan_available": _HDBSCAN_AVAILABLE,
            },
        }

    @staticmethod
    def get_cluster_summary(db: Session, run_id: int) -> list[dict[str, Any]]:
        """Get a lightweight cluster summary for dashboard widgets."""
        from sqlalchemy import select

        evidences = db.execute(
            select(RawEvidence).where(RawEvidence.run_id == run_id)
        ).scalars().all()

        texts = [_get_text_for_evidence(ev) for ev in evidences if _get_text_for_evidence(ev)]

        if not texts:
            return []

        summary = []
        for seed in REAL_ESTATE_PAIN_SEEDS:
            count = sum(1 for t in texts if _seed_cluster_score(t, seed["keywords"]) > 0)
            if count > 0:
                summary.append(
                    {
                        "cluster_id": seed["id"],
                        "label": seed["label"],
                        "count": count,
                        "pct": round(count / len(texts) * 100, 1),
                    }
                )

        return sorted(summary, key=lambda x: x["count"], reverse=True)
