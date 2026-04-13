from fastapi import APIRouter

from app.api.v1.evidence import router as evidence_router
from app.api.v1.export import router as export_router
from app.api.v1.final_hardening import router as final_hardening_router
from app.api.v1.health import router as health_router
from app.api.v1.human_review import router as human_review_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.meta import router as meta_router
from app.api.v1.multilingual import router as multilingual_router
from app.api.v1.notion_sync import router as notion_sync_router
from app.api.v1.normalization import router as normalization_router
from app.api.v1.orchestrator import router as orchestrator_router
from app.api.v1.retrieval import router as retrieval_router
from app.api.v1.run_events import router as run_events_router
from app.api.v1.runs import router as runs_router
from app.api.v1.scrape_execution import router as scrape_execution_router
from app.api.v1.system import router as system_router
from app.api.v1.trending import router as trending_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.topic_modeling import router as topic_modeling_router
from app.api.v1.agent_orchestration import router as agent_orchestration_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(meta_router)
api_router.include_router(system_router)
api_router.include_router(runs_router)
api_router.include_router(evidence_router)
api_router.include_router(orchestrator_router)
api_router.include_router(scrape_execution_router)
api_router.include_router(run_events_router)
api_router.include_router(normalization_router)
api_router.include_router(multilingual_router)
api_router.include_router(intelligence_router)
api_router.include_router(retrieval_router)
api_router.include_router(human_review_router)
api_router.include_router(notion_sync_router)
api_router.include_router(export_router)
api_router.include_router(final_hardening_router)
api_router.include_router(trending_router)
api_router.include_router(organizations_router)
api_router.include_router(topic_modeling_router)
api_router.include_router(agent_orchestration_router)