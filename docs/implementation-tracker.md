# Implementation Tracker

## Product
Real Estate Pain Point Intelligence Platform

## Locked Scope
- Public-source scraping for Reddit, app stores, X/Twitter, YouTube, and review sites
- Orchestrator and streaming-aware pipeline
- Raw evidence storage
- Cleaning and normalization
- Multilingual processing
- Journey-stage agent
- Pain-point extraction agent
- Taxonomy and clustering agent
- Root-cause hypothesis agent
- Competitor benchmark agent
- Prioritization agent
- Action recommendation agent
- Human review workflow
- Notion integration
- CSV/JSON/PDF exports
- Highly polished frontend from day one
- No authentication in V1
- Live public-source scraper implementation is intentionally deferred to a later phase; current source scrapers remain deterministic stubs until that phase

## Phase Plan
1. Foundation and skeleton
2. Core backend structure
3. Polished frontend base
4. Database foundation
5. Evidence and run models
6. Orchestrator
7. Source scrapers
8. Streaming pipeline
9. Cleaning and normalization
10. Multilingual pipeline
11. Multi-agent intelligence
12. Vector retrieval
13. Human review
14. Notion integration
15. Export system
16. Final hardening

## Step Status

### Step 0 — Cleanup and reset
Status: Completed

### Step 1 — Repository setup + backend/frontend foundation
Status: Completed

#### Delivered
- Monorepo structure created
- FastAPI backend skeleton created
- Next.js frontend skeleton created
- Root documentation files created
- Implementation tracker created
- Health endpoint added
- Frontend-to-backend health connectivity added
- Initial polished dashboard shell created
- Python package initialization added
- Pytest import path issue resolved via conftest

#### Implemented files
- `.gitignore`
- `Makefile`
- `README.md`
- `docs/architecture.md`
- `docs/implementation-tracker.md`
- `apps/api/pyproject.toml`
- `apps/api/.env.example`
- `apps/api/app/__init__.py`
- `apps/api/app/api/__init__.py`
- `apps/api/app/api/v1/__init__.py`
- `apps/api/app/core/__init__.py`
- `apps/api/app/schemas/__init__.py`
- `apps/api/app/services/__init__.py`
- `apps/api/app/core/config.py`
- `apps/api/app/schemas/health.py`
- `apps/api/app/api/v1/health.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/app/main.py`
- `apps/api/tests/conftest.py`
- `apps/api/tests/test_health.py`
- `apps/web/.env.local.example`
- `apps/web/src/lib/api.ts`
- `apps/web/src/components/status-card.tsx`
- `apps/web/src/components/section-card.tsx`
- `apps/web/src/app/globals.css`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx`

#### Test notes
- Backend health test passing
- Backend root, docs, and health endpoints working
- Frontend dashboard shell loads and shows API status

#### Known issues
- None currently

#### Next step after completion
- Step 2 — Backend app structure hardening

### Step 2 — Backend app structure hardening
Status: Completed

#### Delivered
- Centralized settings model added
- Structured logging setup added
- Lifespan hooks added
- Dependency injection baseline added
- Meta endpoint added
- Common response schemas added
- Expanded backend tests added

#### Implemented files
- `apps/api/app/models/__init__.py`
- `apps/api/app/db/__init__.py`
- `apps/api/app/dependencies/__init__.py`
- `apps/api/app/utils/__init__.py`
- `apps/api/app/core/config.py`
- `apps/api/app/core/logging.py`
- `apps/api/app/core/lifespan.py`
- `apps/api/app/schemas/common.py`
- `apps/api/app/schemas/health.py`
- `apps/api/app/schemas/meta.py`
- `apps/api/app/dependencies/common.py`
- `apps/api/app/api/v1/health.py`
- `apps/api/app/api/v1/meta.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/app/main.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_meta.py`
- `apps/api/tests/test_root.py`

#### Test notes
- Pytest: 3 tests passing
- Root endpoint working
- Health endpoint working
- Meta endpoint working
- Swagger docs working

#### Known issues
- None currently

#### Next step after completion
- Step 3 — Polished frontend application shell

### Step 3 — Polished frontend application shell
Status: Completed

#### Delivered
- Frontend app shell layout added
- Sidebar navigation added
- Top header added
- Richer dashboard hero section added
- Overview stat cards added
- Product scope and surface preview cards added
- Pipeline preview cards added
- API meta integration added on frontend
- Frontend shell upgraded into a product-style dashboard structure

#### Implemented files
- `apps/web/src/types/navigation.ts`
- `apps/web/src/components/ui/app-chip.tsx`
- `apps/web/src/components/app-shell/sidebar.tsx`
- `apps/web/src/components/app-shell/topbar.tsx`
- `apps/web/src/components/dashboard/hero-banner.tsx`
- `apps/web/src/components/dashboard/overview-stat-card.tsx`
- `apps/web/src/components/dashboard/nav-preview-card.tsx`
- `apps/web/src/components/dashboard/pipeline-stage-card.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/app/globals.css`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/package.json`

#### Test notes
- Frontend loads successfully with polished app shell
- Backend-connected status, environment, and version render in UI
- Lint passes successfully

#### Known issues
- Sidebar is optimized for larger screens only in this step
- Navigation is presentational only in this step

#### Next step after completion
- Step 4 — Database foundation

### Step 4 — Database foundation
Status: Completed

#### Delivered
- PostgreSQL docker setup added
- SQLAlchemy base and session added
- DATABASE_URL added to settings
- Alembic initialized
- First migration added
- `system_state` model added
- Database-aware startup check added
- System info endpoint added
- Database foundation test coverage added

#### Implemented files
- `apps/api/.env`
- `apps/api/.env.example`
- `apps/api/docker-compose.yml`
- `apps/api/alembic.ini`
- `apps/api/alembic/env.py`
- `apps/api/alembic/script.py.mako`
- `apps/api/alembic/versions/0001_create_system_state.py`
- `apps/api/app/db/base.py`
- `apps/api/app/db/session.py`
- `apps/api/app/db/models.py`
- `apps/api/app/models/system_state.py`
- `apps/api/app/schemas/system.py`
- `apps/api/app/api/v1/system.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/app/core/config.py`
- `apps/api/app/core/lifespan.py`
- `apps/api/pyproject.toml`
- `apps/api/tests/test_system_info.py`

#### Test notes
- Docker Postgres starts successfully on port 5460
- Alembic migration runs successfully
- Pytest: 4 tests passing
- System info endpoint working
- Backend startup includes DB connection check success

#### Known issues
- Database usage is foundational only in this step
- No business entities beyond `system_state` yet

#### Next step after completion
- Step 5 — Evidence and run models

### Step 5 — Evidence and run models
Status: Completed

#### Delivered
- `scrape_runs` model added
- `raw_evidence` model added
- Alembic migration for runs and evidence added
- Run create/list/get endpoints added
- Evidence create/list/get endpoints added
- DB-backed schemas for runs and evidence added
- API router expanded with run and evidence routes
- Endpoint tests added for runs and evidence

#### Implemented files
- `apps/api/app/models/__init__.py`
- `apps/api/app/models/scrape_run.py`
- `apps/api/app/models/raw_evidence.py`
- `apps/api/app/db/models.py`
- `apps/api/app/schemas/common.py`
- `apps/api/app/schemas/run.py`
- `apps/api/app/schemas/evidence.py`
- `apps/api/app/api/v1/runs.py`
- `apps/api/app/api/v1/evidence.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0002_create_scrape_runs_and_raw_evidence.py`
- `apps/api/tests/test_runs.py`
- `apps/api/tests/test_evidence.py`

#### Test notes
- Alembic migration for scrape runs and raw evidence passes
- Pytest: 6 tests passing
- Run endpoints working
- Evidence endpoints working
- Swagger shows new routes correctly

#### Known issues
- Evidence layer currently stores only raw ingestion-level data
- No cleaning, enrichment, or multilingual normalization yet

#### Next step after completion
- Step 6 — Orchestrator foundation

### Step 6 — Orchestrator foundation
Status: Completed

#### Delivered
- Orchestration fields added to `scrape_runs`
- Orchestrator service added for state transitions
- Dispatch, start, progress, complete, and fail endpoints added
- Active queue endpoint added
- Alembic migration for orchestration fields added
- Tests added for orchestrator lifecycle flows

#### Implemented files
- `apps/api/app/models/scrape_run.py`
- `apps/api/app/schemas/run.py`
- `apps/api/app/schemas/orchestrator.py`
- `apps/api/app/services/orchestrator.py`
- `apps/api/app/api/v1/runs.py`
- `apps/api/app/api/v1/orchestrator.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0003_run_orchestration_fields.py`
- `apps/api/tests/test_orchestrator.py`

#### Test notes
- Alembic migration for orchestration fields passes
- Pytest: 8 tests passing
- Orchestrator endpoints visible in Swagger
- Queue endpoint works
- Run lifecycle transitions work correctly

#### Known issues
- Orchestration is synchronous and API-driven in this step
- No background worker or streaming events yet

#### Next step after completion
- Step 7 — Source scraper foundation

### Step 7 — Source scraper foundation
Status: Completed

#### Delivered
- Generic scraper interface added
- Source-specific scraper modules added for Reddit, YouTube, app reviews, X, and review sites
- Scraper registry added for supported source resolution
- Scrape execution service added
- Scrape execution endpoints added
- Automatic evidence persistence from scraper outputs added
- Source listing endpoint added
- Tests added for source listing and scrape execution flows

#### Implemented files
- `apps/api/app/scrapers/__init__.py`
- `apps/api/app/scrapers/base.py`
- `apps/api/app/scrapers/registry.py`
- `apps/api/app/scrapers/types.py`
- `apps/api/app/scrapers/sources/__init__.py`
- `apps/api/app/scrapers/sources/reddit.py`
- `apps/api/app/scrapers/sources/youtube.py`
- `apps/api/app/scrapers/sources/app_reviews.py`
- `apps/api/app/scrapers/sources/x_posts.py`
- `apps/api/app/scrapers/sources/review_sites.py`
- `apps/api/app/services/scrape_executor.py`
- `apps/api/app/api/v1/scrape_execution.py`
- `apps/api/app/schemas/scrape_execution.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/tests/test_scrape_execution.py`

#### Test notes
- Pytest: 10 tests passing
- Supported source listing endpoint works
- Scrape execution endpoint works
- Evidence is auto-persisted after execution
- Swagger shows scrape-execution routes correctly

#### Known issues
- Scrapers are deterministic stub implementations in this step
- No live external scraping, retries, or rate-limit handling yet

#### Next step after completion
- Step 8 — Streaming pipeline

### Step 8 — Streaming pipeline
Status: Completed

#### Delivered
- `run_events` model added
- Run event schemas added
- Run event service added
- Run event APIs added
- Orchestrator transitions now persist timeline events
- Queue response was refined for streaming-style summaries
- Alembic migration for run events table added
- Tests added for event creation and retrieval flows

#### Implemented files
- `apps/api/app/models/run_event.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/db/models.py`
- `apps/api/app/schemas/run_event.py`
- `apps/api/app/services/run_events.py`
- `apps/api/app/services/orchestrator.py`
- `apps/api/app/api/v1/run_events.py`
- `apps/api/app/schemas/orchestrator.py`
- `apps/api/app/api/v1/orchestrator.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0004_run_events_table.py`
- `apps/api/tests/test_run_events.py`

#### Test notes
- Alembic migration for run events passes
- Pytest: 12 tests passing
- Run-events endpoints visible in Swagger
- Run events are persisted during orchestration flow
- Run timeline retrieval works correctly

#### Known issues
- Event pipeline is persisted and queryable but not yet pushed over WebSockets/SSE
- Frontend is not yet consuming run event streams

#### Next step after completion
- Step 9 — Cleaning and normalization foundation

### Step 9 — Cleaning and normalization foundation
Status: Completed

#### Delivered
- Normalization fields added to `raw_evidence`
- Normalization schemas added
- Normalization service added
- Run normalization APIs added
- Scrape execution now initializes normalization-ready evidence rows
- Deterministic text cleanup, language fallback, and hashing added
- Alembic migration for normalization fields added
- Tests added for normalization flow and evidence output

#### Implemented files
- `apps/api/app/models/raw_evidence.py`
- `apps/api/app/schemas/evidence.py`
- `apps/api/app/api/v1/evidence.py`
- `apps/api/app/services/scrape_executor.py`
- `apps/api/app/schemas/normalization.py`
- `apps/api/app/services/normalization.py`
- `apps/api/app/api/v1/normalization.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0005_raw_evidence_normalization_fields.py`
- `apps/api/tests/test_normalization.py`

#### Test notes
- Alembic migration for normalization fields passes
- Pytest: 14 tests passing
- Normalization endpoints visible in Swagger
- Run normalization flow works correctly
- Normalized fields appear in evidence responses

#### Known issues
- Normalization is deterministic and English-first in this step
- No translation or advanced language-specific normalization yet

#### Next step after completion
- Step 10 — Multilingual pipeline

### Step 10 — Multilingual pipeline
Status: Completed

#### Delivered
- Multilingual fields added to `raw_evidence`
- Multilingual schemas added
- Multilingual service added
- Run multilingual APIs added
- Deterministic script detection, language resolution, and family mapping added
- Bridge text generation added for downstream analysis readiness
- Alembic migration for multilingual fields added
- Tests added for multilingual flow and evidence output
- Tracker updated to note that live public-source scraper implementation is deferred to a later phase

#### Implemented files
- `apps/api/app/models/raw_evidence.py`
- `apps/api/app/schemas/evidence.py`
- `apps/api/app/services/scrape_executor.py`
- `apps/api/app/services/normalization.py`
- `apps/api/app/schemas/multilingual.py`
- `apps/api/app/services/multilingual.py`
- `apps/api/app/api/v1/multilingual.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0006_raw_evidence_multilingual_fields.py`
- `apps/api/tests/test_multilingual.py`

#### Test notes
- Alembic migration for multilingual fields passes
- Pytest: 16 tests passing
- Multilingual endpoints visible in Swagger
- Run multilingual flow works correctly
- Multilingual fields appear in evidence responses

#### Known issues
- Multilingual processing is deterministic and non-LLM in this step
- Live public-source scrapers are still deferred and current scrapers remain deterministic stubs
- No true translation layer yet; bridge text is preparation for later stages

#### Next step after completion
- Step 11 — Multi-agent intelligence

### Step 11 — Multi-agent intelligence
Status: Completed

#### Delivered
- `agent_insights` model added
- Agent insight schemas added
- Multi-agent intelligence service added
- Run intelligence APIs added
- Deterministic outputs added for journey stage, pain point, taxonomy cluster, root cause, competitor label, priority, and action recommendation
- Alembic migration for agent insights table added
- Tests added for intelligence flow and insight retrieval

#### Implemented files
- `apps/api/app/models/agent_insight.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/db/models.py`
- `apps/api/app/schemas/agent_insight.py`
- `apps/api/app/schemas/intelligence.py`
- `apps/api/app/services/intelligence.py`
- `apps/api/app/api/v1/intelligence.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0007_agent_insights_table.py`
- `apps/api/tests/test_intelligence.py`

#### Test notes
- Alembic migration for agent insights passes
- Pytest: 17 tests passing
- Intelligence endpoints visible in Swagger
- Run intelligence flow works correctly
- Insight fields appear in intelligence responses

#### Known issues
- Intelligence layer is deterministic and non-LLM in this step
- Live public-source scrapers are still deferred and current scrapers remain deterministic stubs
- OpenAI-powered hybrid extraction, clustering, and recommendation logic will come later

#### Next step after completion
- Step 12 — Vector retrieval

### Step 12 — Vector retrieval
Status: Completed

#### Delivered
- `retrieval_documents` model added
- Retrieval schemas added
- Retrieval service added
- Run retrieval indexing API added
- Retrieval search API added
- Deterministic token-based relevance scoring added
- Alembic migration for retrieval documents table added
- Tests added for retrieval indexing and search flow

#### Implemented files
- `apps/api/app/models/retrieval_document.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/db/models.py`
- `apps/api/app/schemas/retrieval.py`
- `apps/api/app/services/retrieval.py`
- `apps/api/app/api/v1/retrieval.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0008_retrieval_documents_table.py`
- `apps/api/tests/test_retrieval.py`

#### Test notes
- Alembic migration for retrieval documents passes
- Pytest: 18 tests passing
- Retrieval endpoints visible in Swagger
- Retrieval indexing flow works correctly
- Retrieval search returns scored results

#### Known issues
- Retrieval is deterministic and token-based in this step
- No embeddings or external vector database yet
- Live public-source scrapers are still deferred and current scrapers remain deterministic stubs

#### Next step after completion
- Step 13 — Human review

### Step 13 — Human review
Status: Completed

#### Delivered
- `human_review_queue` model added
- Human review schemas added
- Human review service added
- Review queue generation API added
- Review queue listing API added
- Review approve and reject APIs added
- Alembic migration for human review queue added
- Tests added for human review flow

#### Implemented files
- `apps/api/app/models/human_review_item.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/db/models.py`
- `apps/api/app/schemas/human_review.py`
- `apps/api/app/services/human_review.py`
- `apps/api/app/api/v1/human_review.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0009_human_review_queue_table.py`
- `apps/api/tests/test_human_review.py`

#### Test notes
- Alembic migration for human review queue passes
- Pytest: 19 tests passing
- Human review endpoints visible in Swagger
- Review queue generation works correctly
- Review approval flow works correctly

#### Known issues
- Human review is API-driven only in this step
- No dedicated frontend review console yet
- Live public-source scrapers are still deferred and current scrapers remain deterministic stubs

#### Next step after completion
- Step 14 — Notion integration

### Step 14 — Notion integration
Status: Completed

#### Delivered
- `notion_sync_jobs` model added
- Notion sync schemas added
- Notion sync service added
- Notion sync job generation API added
- Notion sync job listing API added
- Notion sync mark-synced and mark-failed APIs added
- Alembic migration for notion sync jobs added
- Tests added for notion sync flow

#### Implemented files
- `apps/api/app/models/notion_sync_job.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/db/models.py`
- `apps/api/app/schemas/notion_sync.py`
- `apps/api/app/services/notion_sync.py`
- `apps/api/app/api/v1/notion_sync.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0010_notion_sync_jobs_table.py`
- `apps/api/tests/test_notion_sync.py`

#### Test notes
- Alembic migration for notion sync jobs passes
- Pytest: 20 tests passing
- Notion sync endpoints visible in Swagger
- Notion sync job generation works correctly
- Notion sync mark-synced flow works correctly

#### Known issues
- Notion integration is API-driven and simulated in this step
- No real Notion API connector yet
- Live public-source scrapers are still deferred and current scrapers remain deterministic stubs

#### Next step after completion
- Step 15 — Export system

### Step 15 — Export system
Status: Completed

#### Delivered
- `export_jobs` model added
- Export schemas added
- Export service added
- Export job generation API added
- Export job listing API added
- Export mark-completed and mark-failed APIs added
- Alembic migration for export jobs added
- Tests added for export flow

#### Implemented files
- `apps/api/app/models/export_job.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/db/models.py`
- `apps/api/app/schemas/export.py`
- `apps/api/app/services/export.py`
- `apps/api/app/api/v1/export.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/alembic/versions/0011_export_jobs_table.py`
- `apps/api/tests/test_export.py`

#### Test notes
- Alembic migration for export jobs passes
- Pytest: 21 tests passing
- Export endpoints visible in Swagger
- Export job generation works correctly
- Export mark-completed flow works correctly

#### Known issues
- Export system is API-driven and simulated in this step
- No real file-generation pipeline yet
- Live public-source scrapers are still deferred and current scrapers remain deterministic stubs

#### Next step after completion
- Step 16 — Final hardening

### Step 16 — Final hardening
Status: Completed

#### Delivered
- Final hardening service added for cross-pipeline validation and readiness checks
- Run readiness API added
- System overview API added
- Guardrails added to prevent downstream stages from running without prerequisites
- Export generation now blocks when no evidence exists
- Retrieval indexing now blocks when evidence or intelligence outputs are missing
- Human review generation now blocks when insights are missing
- Notion sync generation now blocks when approved review items are missing
- Tests added for readiness summary and downstream guardrails

#### Implemented files
- `apps/api/app/services/final_hardening.py`
- `apps/api/app/schemas/final_hardening.py`
- `apps/api/app/api/v1/final_hardening.py`
- `apps/api/app/services/retrieval.py`
- `apps/api/app/services/human_review.py`
- `apps/api/app/services/notion_sync.py`
- `apps/api/app/services/export.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/tests/test_final_hardening.py`

#### Test notes
- Pytest passes with final hardening coverage added
- Final-hardening endpoints visible in Swagger
- Run readiness summary works correctly
- System overview works correctly
- Downstream guardrails correctly block invalid pipeline transitions

#### Known issues
- Live public-source scrapers are still deferred and current scrapers remain deterministic stubs
- Final hardening is API/backend focused; no dedicated frontend operational console yet
- Export and Notion flows remain simulated and do not yet call real external services

#### Next step after completion
- Locked V1 backend scope completed

---

## Locked Scope — V2
- Real live scraper implementation
- Real export generation
- Real Notion integration
- Embedding-based retrieval
- LLM-assisted intelligence layer
- Review console backend readiness
- Pipeline observability and run diagnostics
- Full frontend product console
- Multi-tenant architecture

## Explicitly Out of V2 Scope
- Advanced clustering/topic modeling beyond practical need
- Automated agent orchestration with many LLM agents talking to each other

## V2 Phase Plan
17. Real ingestion foundation + first live connector
18. Remaining live source connectors
19. Real export generation
20. Real Notion integration
21. Embedding retrieval foundation
22. Hybrid LLM-assisted intelligence
23. Review console backend readiness
24. Pipeline observability and diagnostics
25. Full frontend product console
26. Multi-tenant architecture foundation

### Step 17 — Real ingestion foundation + first live connector
Status: Completed

#### Delivered
- Live-capable scraper settings added
- Shared scraper HTTP client added
- Scraper utility helpers added
- Real-ingestion metadata fields added to `raw_evidence`
- Source query, fetch timestamp, parser version, dedupe key, and raw payload snapshot persistence added
- Evidence API updated to support ingestion metadata fields
- Legacy evidence compatibility handling added for newly introduced JSON payload field
- Source-level deduplication support added in scrape execution flow
- Scrape execution response updated with deduplication-aware output
- First live connector foundation added for Reddit public ingestion
- Tests added for Reddit live scraper behavior and ingestion metadata flow

#### Implemented files
- `apps/api/app/core/config.py`
- `apps/api/.env.example`
- `apps/api/.env`
- `apps/api/app/models/raw_evidence.py`
- `apps/api/app/schemas/evidence.py`
- `apps/api/app/api/v1/evidence.py`
- `apps/api/app/scrapers/base.py`
- `apps/api/app/scrapers/types.py`
- `apps/api/app/scrapers/utils.py`
- `apps/api/app/scrapers/http_client.py`
- `apps/api/app/scrapers/registry.py`
- `apps/api/app/scrapers/sources/reddit.py`
- `apps/api/app/services/scrape_executor.py`
- `apps/api/app/schemas/scrape_execution.py`
- `apps/api/app/api/v1/scrape_execution.py`
- `apps/api/alembic/versions/0012_raw_evidence_ingestion_metadata.py`
- `apps/api/tests/test_scrape_execution.py`
- `apps/api/tests/test_evidence.py`
- `apps/api/tests/test_reddit_live_scraper.py`

#### Test notes
- Alembic migration for ingestion metadata passes
- Legacy DB rows were backfilled for `raw_payload_json`
- Pytest: 24 tests passing
- Evidence endpoints return ingestion metadata correctly
- Scrape execution persists ingestion metadata successfully
- Deduplication-aware scrape execution response works correctly
- Reddit live-ingestion foundation behaves correctly in tests

#### Known issues
- Only the first live connector foundation is completed in this step
- Remaining live connectors are still pending for V2 Step 18
- Real network variability, rate-limit behavior, and provider-specific fallbacks will deepen further in the next step

#### Next step after completion
- Step 18 — Remaining live source connectors

### Step 18 — Remaining live source connectors
Status: Completed

#### Delivered
- Live-capable YouTube connector foundation added
- Live-capable app reviews connector foundation added
- Live-capable public social fallback connector added for X-constrained scenarios
- Live-capable review sites connector foundation added
- Shared scraper HTTP client extended to support text fetches in addition to JSON fetches
- Shared scraper utility layer expanded with HTML stripping and slug generation helpers
- All remaining source connectors now follow retry/fallback/live-or-stub execution patterns
- Tests added for YouTube, app reviews, public social fallback, and review-site live parsing flows

#### Implemented files
- `apps/api/app/core/config.py`
- `apps/api/.env.example`
- `apps/api/.env`
- `apps/api/app/scrapers/http_client.py`
- `apps/api/app/scrapers/utils.py`
- `apps/api/app/scrapers/sources/youtube.py`
- `apps/api/app/scrapers/sources/app_reviews.py`
- `apps/api/app/scrapers/sources/x_posts.py`
- `apps/api/app/scrapers/sources/review_sites.py`
- `apps/api/tests/test_youtube_live_scraper.py`
- `apps/api/tests/test_app_reviews_live_scraper.py`
- `apps/api/tests/test_x_live_scraper.py`
- `apps/api/tests/test_review_sites_live_scraper.py`

#### Test notes
- Pytest passes with Step 18 connector coverage added
- YouTube live parsing behavior works in tests
- App reviews live parsing behavior works in tests
- Public social fallback parsing behavior works in tests
- Review sites live parsing behavior works in tests

#### Known issues
- YouTube and review-site parsing still depend on brittle public-page structures and may need provider-specific strengthening in later iterations
- X direct access is still constrained, so the connector uses a public social fallback strategy rather than official X ingestion
- Live scraper reliability will continue improving as observability and diagnostics are added in later V2 steps

#### Next step after completion
- Step 19 — Real export generation