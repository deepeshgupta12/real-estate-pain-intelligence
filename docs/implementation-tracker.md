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

### Step 6 — Orchestrator foundation
Status: Completed

#### Delivered
- Orchestration fields added to `scrape_runs`
- Orchestrator service added for state transitions
- Dispatch, start, progress, complete, and fail endpoints added
- Active queue endpoint added
- Alembic migration for orchestration fields added
- Tests added for orchestrator lifecycle flows

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
27. Advanced clustering/topic modeling beyond practical need
28. Automated agent orchestration with many LLM agents talking to each other

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

### Step 19 — Real export generation
Status: Completed

#### Delivered
- Real CSV export generation added
- Real JSON export generation added
- Real PDF export generation added
- Run-level export packaging added for:
  - raw evidence
  - normalized and multilingual-ready evidence fields
  - agent insights
  - retrieval documents
  - human review items
  - notion sync jobs
- Export output directory setting added
- Export artifact metadata fields added to export jobs
- File path, file size, generated timestamp, and row-count persistence added
- PDF executive summary generation added
- Export generation now produces real completed artifacts instead of simulated jobs
- Export test coverage updated for real artifact validation

### Step 20 — Real Notion integration
Status: Completed

#### Delivered
- Real Notion client integration added
- Config-driven Notion destination support added for:
  - database mode
  - page mode
- Notion API settings added to backend configuration
- Real sync execution endpoint added for individual sync jobs
- Real sync execution endpoint added for run-level sync batches
- Idempotency protection added using stable sync keys per approved review item
- Existing synced jobs are now preserved and not re-created unnecessarily
- Retry-aware sync lifecycle added
- Notion sync metadata and real payload packaging added
- Manual mark-synced and mark-failed endpoints retained
- Real Notion integration test coverage added

### Step 21 — Embedding retrieval foundation
Status: Completed

#### Delivered
- Embedding service added for deterministic embedding generation
- Retrieval indexing upgraded from token-only indexing to embedding-backed indexing
- Embedding metadata fields added to retrieval documents
- Native pgvector column added
- Two-step migration path added
- Retrieval search upgraded to embedding similarity scoring
- Backend config added for embedding provider/model/dimensions and retrieval defaults
- Docker Postgres image upgraded to pgvector-enabled image
- Native pgvector extension verified in local Postgres
- Tests updated and passing for embedding-backed retrieval flow

### Step 22 — Hybrid LLM-assisted intelligence
Status: Completed

#### Delivered
- Hybrid intelligence mode added with deterministic baseline + optional LLM refinement
- OpenAI-backed LLM intelligence configuration added
- Official OpenAI SDK dependency added
- LLM intelligence service added
- Intelligence pipeline upgraded with fallback behavior
- Intelligence response expanded with llm and deterministic counts
- Insight metadata persisted for baseline/final/LLM state
- Test coverage added for deterministic, LLM-assisted, and fallback flows

### Step 23 — Review console backend readiness
Status: Completed

#### Delivered
- Review summary endpoint added for frontend console headers and dashboard stats
- Enriched queue listing added with filters for:
  - review status
  - reviewer decision
  - priority
  - analysis mode
- Review detail endpoint added with joined insight and evidence context
- Bulk approve and bulk reject endpoints added
- Review queue payload enriched using insight and evidence metadata
- Final hardening readiness upgraded with review-console-specific checks and counts

### Step 24 — Pipeline observability and diagnostics
Status: Completed

#### Delivered
- Enriched run-events filtering added by:
  - run
  - event type
  - stage
  - status
  - limit
  - offset
  - ordering
- Queue health summaries added with:
  - latest event snapshot
  - heartbeat age
  - stale-run detection
  - health labels
- Run diagnostics endpoint added with:
  - latest event
  - stage timeline
  - readiness snapshot
  - failure snapshot
  - stale/health metadata
- Observability overview endpoint added with:
  - active queue count
  - stale active runs count
  - recent failed runs count
  - recent event volume
  - review backlog count
  - run status/stage distributions
- Final hardening count compatibility expanded for observability use
- Test coverage added for diagnostics, filtering, stale detection, and observability summaries

### Step 25 — Full frontend product console
Status: Completed

#### Delivered
- Frontend shell upgraded into a real product console using live backend data
- Overview dashboard now renders live:
  - health
  - meta
  - final hardening overview
  - observability overview
- Queue health section added for active runs and stale-run visibility
- Run diagnostics section added with run-id based inspection
- Run events explorer added with interactive filtering
- Review console section added with:
  - summary stats
  - queue filtering
  - joined detail view
  - approve / reject actions
  - bulk approve / bulk reject actions
- Sidebar navigation upgraded to real section navigation
- Frontend now reflects the backend capabilities built through Steps 1–24

#### Implemented files
- `apps/web/package.json`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/globals.css`
- `apps/web/src/lib/api.ts`
- `apps/web/src/types/navigation.ts`
- `apps/web/src/components/app-shell/sidebar.tsx`
- `apps/web/src/components/app-shell/topbar.tsx`
- `apps/web/src/components/dashboard/hero-banner.tsx`
- `apps/web/src/components/dashboard/overview-stat-card.tsx`
- `apps/web/src/components/dashboard/nav-preview-card.tsx`
- `apps/web/src/components/dashboard/pipeline-stage-card.tsx`
- `apps/web/src/components/console/section-shell.tsx`
- `apps/web/src/components/console/queue-health-panel.tsx`
- `apps/web/src/components/console/run-diagnostics-panel.tsx`
- `apps/web/src/components/console/run-events-panel.tsx`
- `apps/web/src/components/console/review-console-panel.tsx`
- `docs/implementation-tracker.md`

#### Test notes
- Frontend build passes successfully with current Next.js setup
- Console uses existing Step 23 and Step 24 backend APIs directly
- No extra frontend dependency was introduced
- Interactive review actions are wired against live backend routes

#### Known issues
- Frontend uses direct browser-to-backend calls and assumes backend is reachable on configured API base URL
- CORS middleware is required on the backend for browser-driven approve / reject and bulk review actions
- No authentication or role-based UI constraints yet
- Pagination is basic and can be expanded later
- Additional sections for evidence explorer, retrieval explorer, and export center can be added in later steps

### Step 26A — Full pipeline action workspace
Status: In Progress

#### Delivered in this implementation
- Frontend run setup section added with:
  - create new run
  - load existing run
  - friendlier labels and placeholders
- Current run summary section added with:
  - basic run details
  - readiness snapshot
  - easier wording
- Pipeline progress tracker added with:
  - human-friendly stage names
  - completed / next focus / pending states
- Pipeline action section added for:
  - start data collection
  - clean text
  - prepare language support
  - generate insights
  - prepare search-ready knowledge
  - create review list
  - prepare Notion sync
  - run Notion sync
  - create files
  - check final readiness
- Workspace-wide refresh flow added so monitoring sections can be refreshed after actions
- Info-tip component added to explain terms in simple language
- Existing queue health, diagnostics, events, and review console remain available below the new action workspace
- Existing backend APIs are reused for Step 26A, so no new backend endpoints are required

#### Implemented files
- `apps/web/src/app/page.tsx`
- `apps/web/src/lib/api.ts`
- `apps/web/src/components/app-shell/sidebar.tsx`
- `apps/web/src/components/app-shell/topbar.tsx`
- `apps/web/src/components/ui/info-tip.tsx`
- `apps/web/src/components/console/workspace-shell.tsx`
- `apps/web/src/components/console/run-setup-panel.tsx`
- `apps/web/src/components/console/current-run-panel.tsx`
- `apps/web/src/components/console/pipeline-progress-panel.tsx`
- `apps/web/src/components/console/pipeline-actions-panel.tsx`
- `docs/implementation-tracker.md`

#### Test notes
- This step should allow the frontend to operate the run flow instead of only observing it
- Existing backend action endpoints are expected to be available and reachable from the browser
- Review moderation should keep working as before
- Notion sync execution still depends on backend configuration and approved review items
- Export generation still depends on evidence existing for the selected run

#### Next step after confirmation
- Step 26B — optional deeper output workspaces such as evidence explorer, retrieval explorer, export center, and richer stage-level result views

### Step 26A — Full pipeline action workspace
Status: Completed

#### Delivered
- Frontend run setup section added with:
  - create new run
  - load existing run
  - friendlier labels and placeholders
- Current run summary section added with:
  - basic run details
  - readiness snapshot
  - easier wording
- Pipeline progress tracker added with:
  - human-friendly stage names
  - completed / next focus / pending states
- Pipeline action section added for:
  - start data collection
  - clean text
  - prepare language support
  - generate insights
  - prepare search-ready knowledge
  - create review list
  - prepare Notion sync
  - run Notion sync
  - create files
  - check final readiness
- Workspace-wide refresh flow added so monitoring sections can be refreshed after actions
- Info-tip component added to explain terms in simple language
- Existing queue health, diagnostics, events, and review console remain available below the new action workspace
- Existing backend APIs are reused for Step 26A, so no new backend endpoints are required

### Step 26B — Run-scoped review workspace enhancements
Status: Completed

#### Delivered
- Initial page load updated to fetch review summary and queue for the preferred active run instead of mixed global review data
- Workspace refresh flow updated to keep review summary and queue aligned with the selected run
- Review console upgraded with:
  - active-run default scoping
  - explicit run scope switching
  - clearer analysis mode visibility
  - clearer live vs stub fetch-mode visibility
  - source-level visibility in the queue
  - richer joined review detail state
- Current run summary upgraded with review signal snapshot showing:
  - live-backed items
  - stub-backed items
  - unknown fetch-mode items
  - LLM-used insights
  - non-LLM insights
- Frontend build intent for this step is to reduce confusion caused by cross-run moderation context and make live-versus-fallback behavior easier to inspect

#### Implemented files
- `apps/web/src/app/page.tsx`
- `apps/web/src/components/console/workspace-shell.tsx`
- `apps/web/src/components/console/current-run-panel.tsx`
- `apps/web/src/components/console/review-console-panel.tsx`

#### Test notes
- Review console should now default to the selected run instead of showing mixed items from older runs
- Refreshing the workspace after any pipeline action should keep review summary and review queue run-scoped
- Review detail should now expose analysis mode, LLM flags, and evidence fetch mode more clearly
- This step is frontend-focused and does not change backend scraper behavior by itself

### Step 26B.1 + Step 26B.2 — Workspace UX reset + review moderation redesign
Status: Completed

#### Delivered
- Workspace visual hierarchy redesigned to reduce clutter and improve operator usability
- Sidebar simplified into a cleaner navigation surface with less competing content
- Topbar rewritten to behave like an operational header instead of a marketing banner
- Overview area redesigned into a compact workspace summary with clearer system context
- Stat cards and preview cards restyled with lighter visual weight and better scanning
- Section shell redesigned for more consistent spacing and stronger section separation
- Run setup panel redesigned for cleaner create/load flow
- Current run panel redesigned into:
  - cleaner identity strip
  - compact run details
  - readiness summary
  - signal-quality summary
- Pipeline progress redesigned into a clearer stage tracker
- Pipeline actions redesigned into grouped operational sections:
  - collection and preparation
  - analysis and indexing
  - sync and output
- Queue health redesigned with cleaner table styling and better health visibility
- Run diagnostics redesigned with:
  - lighter filter header
  - clearer latest-event and failure panels
  - cleaner timeline table
  - cleaner readiness views
- Run events explorer redesigned with cleaner filters and more readable event table
- Review console fully redesigned with:
  - summary metric strip
  - clearer scope switching
  - cleaner filter bar
  - improved reviewer notes area
  - cleaner queue table
  - stronger selected-row behavior
  - easier-to-read review detail panel
  - clearer moderation actions
  - improved badges for decision, priority, and fetch mode
- Existing backend APIs remained sufficient; no backend endpoint changes were required for this step

#### Implemented files
- `apps/web/src/app/globals.css`
- `apps/web/src/components/app-shell/sidebar.tsx`
- `apps/web/src/components/app-shell/topbar.tsx`
- `apps/web/src/components/dashboard/hero-banner.tsx`
- `apps/web/src/components/dashboard/nav-preview-card.tsx`
- `apps/web/src/components/dashboard/overview-stat-card.tsx`
- `apps/web/src/components/dashboard/pipeline-stage-card.tsx`
- `apps/web/src/components/console/section-shell.tsx`
- `apps/web/src/components/console/workspace-shell.tsx`
- `apps/web/src/components/console/run-setup-panel.tsx`
- `apps/web/src/components/console/current-run-panel.tsx`
- `apps/web/src/components/console/pipeline-progress-panel.tsx`
- `apps/web/src/components/console/pipeline-actions-panel.tsx`
- `apps/web/src/components/console/queue-health-panel.tsx`
- `apps/web/src/components/console/run-diagnostics-panel.tsx`
- `apps/web/src/components/console/run-events-panel.tsx`
- `apps/web/src/components/console/review-console-panel.tsx`
- `apps/web/src/components/ui/info-tip.tsx`

#### Test notes
- This step is frontend-only
- Existing run, review, observability, and readiness APIs are reused
- Review console should stay scoped to the active run by default
- Queue and detail moderation flows should continue to work with the existing backend routes
- Frontend lint and build should be run after replacing the files

#### Next step after confirmation
- Step 26C — evidence explorer, retrieval explorer, export center, and richer result-surface views per pipeline stage