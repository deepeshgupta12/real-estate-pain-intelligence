import re
from collections import Counter

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.agent_insight import AgentInsight
from app.models.raw_evidence import RawEvidence
from app.models.retrieval_document import RetrievalDocument
from app.models.scrape_run import ScrapeRun
from app.services.orchestrator import OrchestratorService


class RetrievalService:
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s]+", " ", text.lower())
        return [token for token in cleaned.split() if token]

    @staticmethod
    def _token_count(text: str) -> int:
        return len(RetrievalService._tokenize(text))

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
        run = OrchestratorService.get_run_or_404(db, run_id)

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
            orchestrator_notes="Retrieval indexing started",
        )

        for evidence in evidence_items:
            insight = insight_by_evidence_id.get(evidence.id)
            title, document_text = RetrievalService._build_document_text(evidence, insight)

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
                metadata_json={
                    "source_name": evidence.source_name,
                    "platform_name": evidence.platform_name,
                    "pain_point_label": insight.pain_point_label if insight else None,
                    "priority_label": insight.priority_label if insight else None,
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
            orchestrator_notes="Retrieval indexing completed",
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
    def _score(query_tokens: list[str], document_text: str) -> float:
        doc_tokens = RetrievalService._tokenize(document_text)
        if not query_tokens or not doc_tokens:
            return 0.0

        doc_counter = Counter(doc_tokens)
        score = 0.0

        for token in query_tokens:
            if token in doc_counter:
                score += 1.0 + (0.1 * doc_counter[token])

        return score

    @staticmethod
    def search(
        db: Session,
        query: str,
        top_k: int = 5,
        run_id: int | None = None,
    ) -> list[tuple[RetrievalDocument, float]]:
        stmt = select(RetrievalDocument)

        if run_id is not None:
            stmt = stmt.where(RetrievalDocument.scrape_run_id == run_id)

        rows = db.scalars(stmt.order_by(RetrievalDocument.id.asc())).all()

        query_tokens = RetrievalService._tokenize(query)
        scored_rows: list[tuple[RetrievalDocument, float]] = []

        for row in rows:
            score = RetrievalService._score(query_tokens, row.document_text)
            if score > 0:
                scored_rows.append((row, score))

        scored_rows.sort(key=lambda item: item[1], reverse=True)
        return scored_rows[:top_k]