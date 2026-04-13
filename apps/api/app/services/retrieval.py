from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.agent_insight import AgentInsight
from app.models.raw_evidence import RawEvidence
from app.models.retrieval_document import RetrievalDocument
from app.models.scrape_run import ScrapeRun
from app.services.embeddings import EmbeddingService
from app.services.final_hardening import FinalHardeningService
from app.services.orchestrator import OrchestratorService


class RetrievalService:
    @staticmethod
    def _token_count(text: str) -> int:
        return len(EmbeddingService._tokenize(text))

    @staticmethod
    def _build_document_text(
        evidence: RawEvidence,
        insight: AgentInsight | None,
    ) -> tuple[str | None, str]:
        title = None
        evidence_text = (
            evidence.bridge_text
            or evidence.normalized_text
            or evidence.cleaned_text
            or evidence.raw_text
        )

        parts = [evidence_text]

        if insight is not None:
            title = insight.pain_point_label
            insight_parts = [
                insight.journey_stage or "",
                insight.pain_point_label or "",
                insight.pain_point_summary or "",
                insight.taxonomy_cluster or "",
                insight.root_cause_hypothesis or "",
                insight.competitor_label or "",
                insight.priority_label or "",
                insight.action_recommendation or "",
            ]
            parts.extend(part for part in insight_parts if part)

        document_text = " | ".join(part.strip() for part in parts if part and part.strip())
        return title, document_text

    @staticmethod
    def index_run(db: Session, run_id: int) -> tuple[ScrapeRun, int]:
        settings = get_settings()
        run = FinalHardeningService.ensure_run_not_failed(db, run_id)
        FinalHardeningService.ensure_evidence_exists(db, run_id)
        FinalHardeningService.ensure_insights_exist(db, run_id)

        evidence_items = db.scalars(
            select(RawEvidence)
            .where(RawEvidence.scrape_run_id == run_id)
            .order_by(RawEvidence.id.asc())
        ).all()

        insight_rows = db.scalars(
            select(AgentInsight)
            .where(AgentInsight.scrape_run_id == run_id)
            .order_by(AgentInsight.id.asc())
        ).all()

        insight_by_evidence_id = {row.raw_evidence_id: row for row in insight_rows}

        db.execute(delete(RetrievalDocument).where(RetrievalDocument.scrape_run_id == run_id))
        db.commit()

        indexed_count = 0

        OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="retrieval_indexing",
            orchestrator_notes="Embedding retrieval indexing started",
        )

        for evidence in evidence_items:
            insight = insight_by_evidence_id.get(evidence.id)
            title, document_text = RetrievalService._build_document_text(evidence, insight)
            embedding_vector = EmbeddingService.embed_text(document_text)

            retrieval_document = RetrievalDocument(
                scrape_run_id=run_id,
                raw_evidence_id=evidence.id,
                agent_insight_id=insight.id if insight else None,
                title=title,
                document_text=document_text,
                document_type="evidence_insight_bundle" if insight else "evidence_only",
                language_code=evidence.resolved_language or evidence.normalized_language or evidence.language,
                retrieval_status="indexed",
                token_count=RetrievalService._token_count(document_text),
                embedding_status="embedded",
                embedding_model_name=settings.embedding_model_name,
                embedding_dimensions=settings.embedding_dimensions,
                embedding_vector_json=embedding_vector,
                embedding_vector=embedding_vector,
                embedded_at=datetime.now(timezone.utc),
                metadata_json={
                    "source_name": evidence.source_name,
                    "platform_name": evidence.platform_name,
                    "pain_point_label": insight.pain_point_label if insight else None,
                    "priority_label": insight.priority_label if insight else None,
                    "embedding_provider": settings.embedding_provider,
                },
            )
            db.add(retrieval_document)
            indexed_count += 1

        db.commit()

        run = OrchestratorService.update_progress(
            db=db,
            run_id=run_id,
            pipeline_stage="retrieval_indexed",
            items_processed=run.items_processed,
            orchestrator_notes="Embedding retrieval indexing completed",
        )

        return run, indexed_count

    @staticmethod
    def list_run_documents(db: Session, run_id: int) -> list[RetrievalDocument]:
        rows = db.scalars(
            select(RetrievalDocument)
            .where(RetrievalDocument.scrape_run_id == run_id)
            .order_by(RetrievalDocument.id.asc())
        ).all()
        return list(rows)

    @staticmethod
    def search(
        db: Session,
        query: str,
        top_k: int = 5,
        run_id: int | None = None,
    ) -> list[tuple[RetrievalDocument, float]]:
        settings = get_settings()
        effective_top_k = top_k or settings.retrieval_search_default_top_k
        query_vector = EmbeddingService.embed_query(query)

        distance_expr = RetrievalDocument.embedding_vector.cosine_distance(query_vector)
        score_expr = (1 - distance_expr).label("score")

        stmt = (
            select(RetrievalDocument, score_expr)
            .where(RetrievalDocument.embedding_status == "embedded")
            .where(RetrievalDocument.embedding_vector.is_not(None))
        )

        if run_id is not None:
            stmt = stmt.where(RetrievalDocument.scrape_run_id == run_id)

        stmt = stmt.order_by(distance_expr.asc(), RetrievalDocument.id.asc()).limit(effective_top_k)

        rows = db.execute(stmt).all()

        results: list[tuple[RetrievalDocument, float]] = []
        for row, score in rows:
            numeric_score = max(0.0, float(score or 0.0))
            results.append((row, numeric_score))

        return results