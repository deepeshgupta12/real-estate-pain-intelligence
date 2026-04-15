# Real Estate Pain Point Intelligence Platform

An end-to-end AI-powered platform that scrapes public sources across the Indian real estate market, extracts and clusters customer pain points using a multi-agent LLM pipeline, and surfaces actionable competitive intelligence through a polished operator console.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup (Development)](#local-setup-development)
- [Docker Setup (Production-like)](#docker-setup-production-like)
- [Environment Variables](#environment-variables)
- [Running the Platform](#running-the-platform)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [Data Sources](#data-sources)
- [Intelligence Pipeline](#intelligence-pipeline)
- [Frontend Console](#frontend-console)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Background Tasks](#background-tasks)
- [Authentication](#authentication)
- [Observability](#observability)
- [Exports](#exports)
- [Notion Integration](#notion-integration)
- [Trending & Fingerprinting](#trending--fingerprinting)
- [Topic Modeling](#topic-modeling)
- [Multi-Tenant Organizations](#multi-tenant-organizations)
- [Changelog](#changelog)

---

## Overview

The platform answers a single question for real estate brands operating in India:

> **What are customers actually complaining about — and why?**

It does this end-to-end: **scrape → clean → analyse → cluster → prioritise → act.**

A single session targets one brand (e.g. "Square Yards", "NoBroker", "MagicBricks") across all configured public sources. The multi-agent pipeline then extracts pain points, clusters them into a taxonomy, generates root-cause hypotheses, benchmarks against competitors, and produces prioritised action recommendations — all surfaced in a streaming operator console.

**What makes this different from a simple dashboard:**

The platform is designed for product intelligence teams who need to move from raw user complaints to board-ready insight in one automated pipeline run. It handles Indian market specifics including Hinglish content, Hindi-language app reviews, and regional subreddits.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Next.js 15 Frontend                         │
│                                                                     │
│  New Session · Step Progress · Run Steps · Pain Points              │
│  Evidence Explorer · Semantic Search · Review Queue                 │
│  Activity Log · Session Details · Exports · Notion Sync             │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ REST API + SSE streaming
┌───────────────────────────▼─────────────────────────────────────────┐
│                       FastAPI Backend (Python 3.11)                 │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │    Scrapers      │  │   Orchestrator  │  │    AI Agents        │ │
│  │  Reddit (PRAW)   │  │   Pipeline mgr  │  │  Pain Extraction    │ │
│  │  YouTube (API)   │  │   SSE events    │  │  Taxonomy Builder   │ │
│  │  Google Play     │  │   Stage guards  │  │  Root Cause         │ │
│  │  Apple Store     │  │   Run lifecycle │  │  Competitor Bench   │ │
│  │  HackerNews      │  │                 │  │  Priority Scoring   │ │
│  │  Review Sites    │  │                 │  │  Action Advisor     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
│                                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  ARQ + Redis     │  │  pgvector RAG   │  │  Observability      │ │
│  │  Background jobs │  │  Semantic index │  │  Prometheus metrics │ │
│  │  7 task types    │  │  Cosine search  │  │  Sentry errors      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
└──────────┬──────────────────────────────────────────┬───────────────┘
           │                                          │
┌──────────▼──────────┐                    ┌──────────▼──────────┐
│   PostgreSQL 16      │                    │     OpenAI API       │
│   + pgvector ext.    │                    │   gpt-4o-mini LLM    │
│   port 5460 (dev)    │                    │   Embeddings         │
└─────────────────────┘                    └─────────────────────┘
```

---

## Features

### Data Collection — 5 sources, multi-tier fallback

**Reddit** (3 tiers): PRAW official API → PullPush.io Pushshift-compatible archive (no auth) → RSS feed → curated stubs. Searches `indianrealestate`, `realestateindia`, `mumbai`, `bangalore`, `delhi`, `pune`, `hyderabad` + global subreddits. Posts + top 3 comments per post.

**YouTube** (2 tiers): YouTube Data API v3 (verified channel IDs for all major brands) → yt-dlp channel scraper → curated stubs. Complaint-focused search queries, `maxResults` capped at 50 to respect the API hard limit.

**Google Play Store** (2 tiers): `google-play-scraper` Python SDK (up to 500 reviews, all languages including Hindi/Hinglish) → HTML fallback. Country code `"in"`, no language filter (captures Hindi-language reviews).

**Apple App Store** (2 tiers): `app-store-scraper` Python library (up to 100 reviews via proper scraper library) → iTunes RSS XML feed (5 pages × 50 reviews = 250 max). No locale filter, covers all Indian users.

**HackerNews / Tech Discussions** (2 tiers): HackerNews Algolia API (`hn.algolia.com`) for proptech and fraud-related discussions → curated stubs. Source labelled `tech_discussions_hn`.

**Review Sites**: Google Play Store SDK + Apple App Store RSS for aggregated review scores.

**Sentiment filtering**: applied at collection time across all sources. Items with rating ≥ 4 AND no negative signal keywords in any language (English + Hindi transliterations: `dhoka`, `bekaar`, `bakwas`, `ghatiya`, `bura`, `nuksaan`) are discarded. Only complaints and mixed-signal content is collected.

**Context-aware scraping**: users attach prebuilt research context chips (Website & Mobile App, Listings, Projects & Builders, Sales Process & Agents, Post-Sales Process, Complaints & Escalations) and optional free-text notes to a session. Keywords are parsed and injected into all scraper queries. App store scrapers (which don't support query filtering) apply post-filtering by context keywords.

**Per-run log files**: `apps/api/logs/run_{id}.log` captures the entire scraping pipeline lifecycle with per-step kept/skipped breakdown, enabling fast debugging without full terminal capture.

**Multi-source sessions**: a single session can select any combination of Reddit, YouTube, App Reviews, Review Sites, and HackerNews. `ScrapeExecutionService` fans out across all selected sources; a failing source is skipped rather than aborting the run.

### Intelligence Pipeline — 7 LLM agents

Hybrid approach: confidence-based routing sends high-confidence signals through the deterministic path (faster, zero API cost) and routes uncertain items to LLM for richer extraction.

**LLM caching**: TTL response cache (24hr, SHA256-keyed, max 10k entries, LRU eviction, thread-safe). Cache hit/miss metrics available via `/api/v1/intelligence/llm-cache-stats`.

**Multi-agent Anthropic orchestration**: 5 specialized agents chained via Anthropic `tool_use` pattern — EvidenceClassifier → PainPointExtractor → RootCauseAnalyst → CompetitorBenchmarker → ActionAdvisor.

**Topic modeling** (BERTopic-inspired, 4-tier graceful degradation): HDBSCAN semantic clustering → NMF matrix factorization → LDA → seed-keyword cluster scoring. 8 predefined real estate pain clusters (inventory_quality, platform_performance, lead_management, trust_and_safety, pricing_transparency, search_discovery, transaction_process, ux_design) always available without ML dependencies.

**Cross-run pain point fingerprinting**: SHA256-keyed `PainPointFingerprint` table tracks recurrence count and rolling weekly buckets (`count_week_0/1/2/3`) across runs. `trend_direction` (rising/stable/declining) computed automatically. `GET /api/v1/trending/top` surfaces the most persistent pain points.

### Console UI — Operator-grade workspace

Real-time SSE streaming for all pipeline step progress. Light theme, fully accessible. 12 major panels, each wrapped in an independent React Error Boundary (one panel crashing never affects others).

**New Session**: brand name input, multi-source platform checkboxes (any combination), research context chips + free-text, recent session list with source icons and archive controls.

**Step Progress**: visual timeline showing completed ✓ / active spinner / pending dots for the 9 pipeline steps.

**Run Steps**: one-click buttons for each pipeline step with dependency gating (downstream steps are disabled until prerequisites succeed).

**Pain Points**: persona-grouped insights (Discovery / Consideration / Conversion / Post-Discovery) with numbered bullets, priority badges (🔴 High / 🟡 Medium / 🟢 Low), taxonomy cluster tags, root cause hypothesis, action recommendation, and per-source breakdown chips.

**Evidence Explorer**: browse all raw posts/reviews/comments for the current run. Filter by source and content type. Full-text client-side search. Expandable cards with "View source ↗" links.

**Semantic Search**: natural language search via pgvector cosine similarity. Sample query chips, score bars (green ≥80%, amber ≥55%), top-K selector (3 / 5 / 10 / 20), run scope toggle.

**Review Queue**: Pending / Approved / Rejected / All filter tabs with live counts (derived from local React state — updates instantly after each action, no backend re-fetch). Bulk approve/reject with Select All. 20-items-per-page pagination. Color-coded cards (green = approved, red = rejected, blue = selected). Inline approve/reject only shown for pending items. `parseSourceSummary()` correctly renders pain point label chip + readable summary text.

**Activity Log**: SSE events explorer with relative timestamps computed client-side only (SSR/hydration-safe), friendly event labels, 60-second auto-refresh.

**Session Details**: run-id based diagnostics — latest event, stage timeline, readiness snapshot, failure snapshot, stale-run detection.

**Exports**: download CSV, JSON, and PDF for the current run with ↓ Download buttons. Auto-refreshes after "Create Exports" step.

### Backend Hardening

**Circuit breakers**: per-source `CircuitBreaker` class (CLOSED → OPEN → HALF_OPEN). 3 failure threshold, 1hr cooldown. Auto-skips blocked sources. Classifies `BLOCKED`, `RATE_LIMITED`, `SERVER_ERROR`, `NOT_FOUND` from HTTP status codes.

**Rate limiting**: SlowAPI middleware, 60 requests/minute per IP. Configurable.

**DB connection pooling**: SQLAlchemy engine with configurable `db_pool_size`, `db_max_overflow`, `db_pool_pre_ping`.

**Input validation**: `target_brand` (max 100 chars, rejects `<>"';\\`), `source_name` allowlist enforced at schema level.

**Pagination**: `GET /api/v1/runs` and `GET /api/v1/evidence` return `{ items, total, limit, offset }`. Archived runs excluded by default.

**Data archiving**: `archived_at` column on `scrape_runs`. Archive/unarchive endpoints. Frontend "Archive" button on non-active sessions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript 5, Tailwind CSS 4 |
| Backend | FastAPI 0.115, Python 3.11, Uvicorn |
| Database | PostgreSQL 16 + pgvector extension |
| ORM / Migrations | SQLAlchemy 2.0, Alembic (21 migrations) |
| AI / LLM | OpenAI `gpt-4o-mini` (chat completions), Anthropic tool_use orchestration |
| Vector embeddings | pgvector (cosine similarity, 128-dim), `sentence-transformers` optional |
| Background jobs | ARQ + Redis 7 |
| Scraping | PRAW, google-play-scraper, app-store-scraper, yt-dlp, httpx |
| Topic modeling | scikit-learn (NMF/LDA), hdbscan (optional), seed clusters (always available) |
| Observability | Prometheus (`prometheus-fastapi-instrumentator`), Sentry SDK |
| Rate limiting | SlowAPI |
| Auth | JWT (`python-jose` + `passlib[bcrypt]`), optional API key middleware |
| Containerization | Docker multi-stage builds, docker compose (6 services) |
| CI/CD | GitHub Actions (pytest, TypeScript check, docker build) |

---

## Project Structure

```
real-estate-pain-intelligence/
├── apps/
│   ├── api/                                   # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/                        # REST endpoints
│   │   │   │   ├── auth.py                    # JWT register/login/refresh/me
│   │   │   │   ├── runs.py                    # Scrape run CRUD + archive
│   │   │   │   ├── evidence.py                # Paginated raw evidence
│   │   │   │   ├── scrape_execution.py        # Trigger scraping per source
│   │   │   │   ├── orchestrator.py            # Pipeline orchestration
│   │   │   │   ├── intelligence.py            # AI agent endpoints
│   │   │   │   ├── retrieval.py               # Semantic search
│   │   │   │   ├── human_review.py            # Review queue
│   │   │   │   ├── notion_sync.py             # Notion integration
│   │   │   │   ├── export.py                  # CSV / JSON / PDF + download
│   │   │   │   ├── trending.py                # Cross-run pain point trends
│   │   │   │   ├── topic_modeling.py          # BERTopic-style topic analysis
│   │   │   │   ├── agent_orchestration.py     # 5-agent Anthropic pipeline
│   │   │   │   ├── organizations.py           # Multi-tenant org management
│   │   │   │   └── router.py
│   │   │   ├── scrapers/
│   │   │   │   ├── base.py                    # BaseScraper interface
│   │   │   │   ├── http_client.py             # RetryingHttpClient (session + jitter)
│   │   │   │   ├── circuit_breaker.py         # CircuitBreaker per source
│   │   │   │   ├── context_utils.py           # Research context → keywords
│   │   │   │   └── sources/
│   │   │   │       ├── reddit.py              # PRAW → PullPush → RSS → stub
│   │   │   │       ├── youtube.py             # Data API v3 → yt-dlp → stub
│   │   │   │       ├── app_reviews.py         # app-store-scraper → iTunes RSS / gps SDK
│   │   │   │       ├── x_posts.py             # HN Algolia → stub
│   │   │   │       └── review_sites.py        # gps SDK → Apple RSS → stub
│   │   │   ├── models/                        # SQLAlchemy ORM models (21 migrations)
│   │   │   ├── schemas/                       # Pydantic request/response schemas
│   │   │   ├── services/
│   │   │   │   ├── scrape_executor.py         # Multi-source fan-out + context injection
│   │   │   │   ├── normalization.py           # Dedup, language detect, content type
│   │   │   │   ├── multilingual.py            # Hinglish detection, bridge text
│   │   │   │   ├── intelligence.py            # Hybrid LLM + deterministic pipeline
│   │   │   │   ├── llm_intelligence.py        # OpenAI chat completions service
│   │   │   │   ├── llm_cache.py               # TTL SHA256 LRU response cache
│   │   │   │   ├── agent_orchestrator.py      # 5-agent Anthropic tool_use service
│   │   │   │   ├── embeddings.py              # sentence-transformers / hash fallback
│   │   │   │   ├── retrieval.py               # pgvector index + cosine search
│   │   │   │   ├── human_review.py            # Review queue generation
│   │   │   │   ├── export.py                  # CSV / JSON / PDF ReportLab generator
│   │   │   │   ├── trending.py                # Pain point fingerprint tracking
│   │   │   │   ├── topic_modeling.py          # NMF/LDA/HDBSCAN + seed clusters
│   │   │   │   ├── notion_sync.py             # Real Notion API client
│   │   │   │   └── run_logger.py              # Per-run log file utility
│   │   │   ├── core/
│   │   │   │   ├── config.py                  # Pydantic settings (60+ config vars)
│   │   │   │   ├── security.py                # JWT create/decode, bcrypt hash
│   │   │   │   └── sentry.py                  # Sentry init
│   │   │   ├── workers/
│   │   │   │   └── tasks.py                   # 7 ARQ async task functions
│   │   │   └── main.py                        # FastAPI app, middleware, lifespan
│   │   ├── alembic/versions/                  # 21 migration files (0001–0021)
│   │   ├── tests/                             # Pytest test suite (100+ tests)
│   │   ├── logs/                              # Per-run log files (auto-created)
│   │   ├── generated_exports/                 # Export artifacts (gitignored)
│   │   ├── docker-compose.yml                 # PostgreSQL + pgvector dev database
│   │   ├── Dockerfile                         # Multi-stage: python:3.11 → python:3.11-slim
│   │   ├── pyproject.toml
│   │   └── .env.example
│   └── web/                                   # Next.js frontend
│       └── src/
│           ├── app/
│           │   ├── layout.tsx
│           │   ├── page.tsx
│           │   └── globals.css                # Design system tokens + utility classes
│           ├── components/
│           │   ├── app-shell/
│           │   │   ├── sidebar.tsx            # 12-item sidebar navigation
│           │   │   └── topbar.tsx             # Brand header + API health indicator
│           │   ├── console/
│           │   │   ├── workspace-shell.tsx    # Root state + Promise.allSettled refresh
│           │   │   ├── run-setup-panel.tsx    # New Session: brand, sources, context chips
│           │   │   ├── current-run-panel.tsx  # Session identity, readiness, signal quality
│           │   │   ├── pipeline-progress-panel.tsx  # 9-step visual timeline
│           │   │   ├── pipeline-actions-panel.tsx   # Gated step execution buttons
│           │   │   ├── pain-points-panel.tsx         # Persona-grouped insights
│           │   │   ├── evidence-explorer-panel.tsx   # Raw evidence browse + search
│           │   │   ├── retrieval-search-panel.tsx    # Semantic search UI
│           │   │   ├── review-console-panel.tsx      # Full review queue with pagination
│           │   │   ├── exports-panel.tsx             # Download CSV / JSON / PDF
│           │   │   ├── queue-health-panel.tsx         # Active sessions compact table
│           │   │   ├── run-diagnostics-panel.tsx      # Stage timeline + failure details
│           │   │   └── run-events-panel.tsx           # Activity log + SSE events
│           │   ├── dashboard/
│           │   │   ├── hero-banner.tsx
│           │   │   ├── overview-stat-card.tsx
│           │   │   ├── nav-preview-card.tsx
│           │   │   └── pipeline-stage-card.tsx
│           │   └── ui/
│           │       ├── info-tip.tsx
│           │       ├── skeleton.tsx
│           │       ├── empty-state.tsx
│           │       └── error-boundary.tsx     # Per-panel crash isolation
│           └── lib/
│               └── api.ts                     # Typed API client (all endpoints)
├── docs/
│   ├── implementation-tracker.md             # Step-by-step delivery log (Steps 0–38)
│   └── architecture.md
├── monitoring/
│   ├── prometheus.yml                         # Scrape config for API metrics
│   └── grafana/                               # Grafana provisioning
├── .github/
│   └── workflows/
│       └── ci.yml                             # Backend tests + TS check + Docker build
└── docker-compose.yml                         # Full stack: postgres, redis, api, worker, web
```

---

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Docker Desktop** (required for PostgreSQL + pgvector; required for the full Docker stack)
- **OpenAI API key** — for LLM analysis steps
- **YouTube Data API v3 key** — free, ~2 minutes to create (see below)
- **Reddit API credentials** — optional; without them, scraper falls back to PullPush.io archive (no auth required)
- **Notion integration token** — optional; required only for Notion sync

---

## Local Setup (Development)

### 1. Clone the repository

```bash
git clone https://github.com/deepeshgupta12/real-estate-pain-intelligence.git
cd real-estate-pain-intelligence
```

### 2. Start the database

```bash
cd apps/api
docker compose up -d postgres
```

This starts PostgreSQL 16 with the pgvector extension on port `5460`. The pgvector extension is enabled automatically via the Docker image.

### 3. Set up the Python backend

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install all dependencies including dev extras
pip install -e ".[dev]"

# Copy and configure environment variables
cp .env.example .env
# Edit .env — minimum required: OPENAI_API_KEY, YOUTUBE_DATA_API_KEY

# Run all 21 database migrations
alembic upgrade head
```

### 4. Set up the Next.js frontend

```bash
cd apps/web
npm install
```

---

## Docker Setup (Production-like)

The root `docker-compose.yml` runs the full stack: PostgreSQL, Redis, API server, ARQ worker, Next.js web, and optional monitoring.

### Build and start all services

```bash
# From the repo root
docker compose build
docker compose up -d
```

Services start on:
- Web console: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5460`
- Redis: `localhost:6379`

### Start with monitoring (Prometheus + Grafana)

```bash
docker compose --profile monitoring up -d
```

Grafana: `http://localhost:3001` (default admin/admin)  
Prometheus: `http://localhost:9090`

### Run migrations inside Docker

```bash
docker compose exec api alembic upgrade head
```

### View per-run scraper logs

```bash
# Follow logs for a specific run
docker compose exec api tail -f apps/api/logs/run_1.log
```

---

## Environment Variables

Copy `apps/api/.env.example` to `apps/api/.env`. Variables marked **Required** must be set before the relevant feature works.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://postgres:postgres@localhost:5460/repi_db` | PostgreSQL connection string |
| `OPENAI_API_KEY` | Yes | — | OpenAI key for LLM analysis |
| `INTELLIGENCE_OPENAI_MODEL` | No | `gpt-4o-mini` | Model used for pain point extraction |
| `YOUTUBE_DATA_API_KEY` | Yes | — | YouTube Data API v3 key (free, 10k units/day) |
| `REDDIT_API_ENABLED` | No | `false` | Set `true` to use PRAW. Without it, falls back to PullPush.io |
| `REDDIT_CLIENT_ID` | No | — | Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | No | — | Reddit app client secret |
| `REDDIT_USER_AGENT` | No | `repi-scraper/1.0` | PRAW user agent string |
| `SCRAPER_FAIL_OPEN_TO_STUB` | No | `false` | `false` = live data only; `true` = allow stubs on source failure |
| `SCRAPER_MAX_ITEMS_PER_SOURCE` | No | `500` | Max items for Reddit/YouTube/HN scrapers |
| `NOTION_API_KEY` | No | — | Notion integration token (`secret_...`) |
| `NOTION_DATABASE_ID` | No | — | Target Notion database ID |
| `NOTION_ENABLE_REAL_SYNC` | No | `false` | Set `true` to push to Notion (dry-run by default) |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis URL for ARQ background jobs |
| `JWT_SECRET_KEY` | No | (placeholder) | JWT signing key. When left as placeholder, dev-mode bypass is active (no token required) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime |
| `API_KEY_ENABLED` | No | `false` | Require `X-API-Key` header on non-public endpoints |
| `API_KEY_SECRET` | No | — | The secret API key value |
| `SENTRY_DSN` | No | — | Sentry DSN for error tracking |
| `PROMETHEUS_ENABLED` | No | `true` | Expose `/metrics` endpoint |
| `EMBEDDING_PROVIDER` | No | `enhanced_hash` | `sentence_transformers` for real semantic embeddings |
| `AGENT_ORCHESTRATOR_ENABLED` | No | `false` | Enable Anthropic 5-agent pipeline |
| `ANTHROPIC_API_KEY` | No | — | Anthropic API key for agent orchestration |
| `TOPIC_MODELING_ENABLED` | No | `true` | Run topic modeling after intelligence step |

### Getting a YouTube Data API v3 key (free, ~2 minutes)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. Enable **YouTube Data API v3** in the API library
3. Go to Credentials → Create Credentials → API Key
4. Paste it into `.env` as `YOUTUBE_DATA_API_KEY`

Free quota: 10,000 units/day ≈ ~100 search requests per day.

### Getting Reddit API credentials (optional)

1. Go to [reddit.com/prefs/apps](https://reddit.com/prefs/apps)
2. Create app → choose "script" type → `redirect_uri: http://localhost:8080`
3. Copy `client_id` (under the app name) and `client_secret` into `.env`
4. Set `REDDIT_API_ENABLED=true` and `REDDIT_USER_AGENT=<yourapp>/1.0`

Without credentials, the Reddit scraper uses PullPush.io (Pushshift-compatible, free, no auth required) as Tier 2, then RSS as Tier 3.

### Getting a Notion integration token (optional)

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration
2. Copy the `secret_...` token as `NOTION_API_KEY`
3. Share your target Notion database with the integration (Share button → invite the integration)
4. Copy the database ID from the URL (the 32-char hex string) as `NOTION_DATABASE_ID`

---

## Running the Platform

### Development — Backend

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API: `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### Development — ARQ Worker (optional — enables background task mode)

```bash
cd apps/api
source .venv/bin/activate
python -m arq app.workers.tasks.WorkerSettings
```

Without the worker running, pipeline action endpoints execute synchronously (acceptable for dev; may timeout for large scrapes).

### Development — Frontend

```bash
cd apps/web
npm run dev
```

Console: `http://localhost:3000`

---

## Pipeline Walkthrough

A full analysis run consists of 9 steps executed in order from the **Run Steps** panel. Each step streams real-time progress events via Server-Sent Events.

| Step | Panel Button | What it does |
|---|---|---|
| 1 | **Collect Feedback** | Scrapes all selected sources. Writes per-run log to `logs/run_{id}.log`. |
| 2 | **Clean Text** | Deduplicates, normalises punctuation, detects language, tags content type. Sentiment signals (emoji, `!!!`) are preserved. |
| 3 | **Prepare Language Support** | Detects Hinglish (Latin-script text with common Hindi words), adds `bridge_text` tag for LLM readiness. |
| 4 | **Generate Insights** | Runs hybrid LLM + deterministic pipeline: pain point extraction, journey stage, taxonomy cluster, root cause hypothesis, competitor label, priority score, action recommendation. Triggers topic modeling and trending fingerprint update automatically. |
| 5 | **Build Search Library** | Embeds all evidence into the pgvector index using 128-dim semantic embeddings (sentence-transformers if available, domain-enhanced hash fallback). |
| 6 | **Create Review List** | Populates the Human Review Queue from `agent_insights` — one queue item per unique pain point. |
| 7 | **Prepare Notion Sync** | Stages approved queue items as Notion sync jobs. |
| 8 | **Run Notion Sync** | Pushes staged jobs to Notion (idempotent — same sync key is never re-created). |
| 9 | **Create Files** | Generates CSV, JSON, and PDF report exports. Files saved to `generated_exports/`. |

---

## Data Sources

| Source | File | Tier 1 | Tier 2 | Tier 3 | Notes |
|---|---|---|---|---|---|
| Reddit | `reddit.py` | PRAW (official API) | PullPush.io archive | RSS feed | Tier 2 requires no credentials |
| YouTube | `youtube.py` | YouTube Data API v3 | yt-dlp channel scraper | Curated stubs | API key required for Tier 1; `maxResults` capped at 50 |
| App Reviews | `app_reviews.py` | `app-store-scraper` (iOS) / `google-play-scraper` (Android) | iTunes RSS (5 pages) | Curated stubs | iOS: up to 100; Android: up to 100; both all-language |
| Review Sites | `review_sites.py` | `google-play-scraper` SDK (500) | Apple RSS (5 pages = 250) | Curated stubs | Context post-filtering applied |
| HackerNews | `x_posts.py` | HN Algolia API | Curated stubs | — | `source_name = "x"` for DB compatibility |

**Brand app IDs (verified):**

| Brand | Play Store ID | App Store ID |
|---|---|---|
| Square Yards | `com.sq.yrd.squareyards` | `1093755061` |
| 99acres | `com.infoedge.android.realestate` | `367516951` |
| MagicBricks | `com.magicbricks.buysellrent` | `457711083` |
| Housing | `com.housing.search` | `863501645` |
| NoBroker | `com.nobroker.app` | `1049714843` |

---

## Intelligence Pipeline

The AI analysis runs via a hybrid pipeline in `intelligence.py`:

**Journey stage classification** — identifies buyer phase: Discovery, Consideration, Conversion, Post-Discovery.

**Pain point extraction** — identifies the specific, discrete complaint from each piece of evidence. High-confidence token matching bypasses LLM; uncertain items use OpenAI `gpt-4o-mini` via `client.chat.completions.create()`.

**Taxonomy clustering** — groups pain points into 8 seed clusters: inventory_quality, platform_performance, lead_management, trust_and_safety, pricing_transparency, search_discovery, transaction_process, ux_design. Optional ML topic modeling (NMF/LDA/HDBSCAN) adds unsupervised clusters.

**Root cause hypothesis** — LLM reasons about the underlying systemic cause per cluster.

**Competitor benchmarking** — compares pain point patterns across different brands in the corpus.

**Priority scoring** — frequency × severity × recency trend composite score.

**Action recommendations** — ranked concrete next steps classified by type (product / engineering / process / investigation / monitoring) and effort (quick_win / medium_term / long_term).

**5-agent Anthropic orchestration** (when `AGENT_ORCHESTRATOR_ENABLED=true`):
- `EvidenceClassifier` → `PainPointExtractor` → `RootCauseAnalyst` → `CompetitorBenchmarker` → `ActionAdvisor`
- Agents chain via Anthropic `tool_use` pattern
- Full TTL response cache (SHA256-keyed) shared with the LLM intelligence service
- Deterministic rule-based fallback when SDK unavailable

All agent outputs stored as `AgentInsight` records and surfaced in the Pain Points panel.

---

## Frontend Console

The console is a single-page workspace at `http://localhost:3000`. Left sidebar has 12 navigation items:

| Sidebar Label | Panel | Purpose |
|---|---|---|
| New Session | `run-setup-panel.tsx` | Brand input, multi-source checkboxes, research context chips, recent sessions |
| Current Session | `current-run-panel.tsx` | Active run identity, stage, readiness snapshot, signal quality (live vs stub vs LLM) |
| Step Progress | `pipeline-progress-panel.tsx` | Visual 9-step timeline |
| Pain Points | `pain-points-panel.tsx` | Persona-grouped insights with priority badges, source chips, root cause + action |
| Run Steps | `pipeline-actions-panel.tsx` | Gated one-click step execution |
| Exports | `exports-panel.tsx` | ↓ Download CSV / JSON / PDF |
| Evidence Explorer | `evidence-explorer-panel.tsx` | Browse raw posts, filter by source/type, full-text search |
| Semantic Search | `retrieval-search-panel.tsx` | Natural language search with score bars |
| Active Sessions | `queue-health-panel.tsx` | Compact 4-column table of running/queued sessions |
| Session Details | `run-diagnostics-panel.tsx` | Stage timeline, latest event, failure details, readiness |
| Activity Log | `run-events-panel.tsx` | SSE event log with relative timestamps |
| Review Queue | `review-console-panel.tsx` | Full moderation interface — filter, approve, reject, bulk actions |

---

## API Reference

Full interactive docs at `http://localhost:8000/docs` when the backend is running.

### Runs

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/runs` | POST | Create a new session (requires auth in prod mode) |
| `/api/v1/runs` | GET | List sessions (`limit`, `offset`, `include_archived`) |
| `/api/v1/runs/{id}` | GET | Get a specific session |
| `/api/v1/runs/{id}/archive` | POST | Archive a session |
| `/api/v1/runs/{id}/unarchive` | POST | Unarchive a session |

### Pipeline

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/scrape-execution/{run_id}` | POST | Execute scraping for selected sources |
| `/api/v1/orchestrator/run/{id}/full` | POST | Execute the full pipeline |
| `/api/v1/orchestrator/run/{id}/stream` | GET | SSE stream of pipeline events |
| `/api/v1/orchestrator/run/{id}/normalize` | POST | Run normalization step |
| `/api/v1/orchestrator/run/{id}/multilingual` | POST | Run multilingual step |
| `/api/v1/intelligence/run/{id}` | POST | Run intelligence step (enqueues ARQ task) |
| `/api/v1/retrieval/run/{id}/index` | POST | Build pgvector search index |
| `/api/v1/retrieval/search` | POST | Semantic search |

### Evidence & Review

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/evidence` | GET | Browse raw evidence (`run_id`, `source_name`, `content_type`, `limit`, `offset`) |
| `/api/v1/human-review/queue` | GET | Fetch review queue (filter by status, priority, analysis mode) |
| `/api/v1/human-review/{id}` | PATCH | Approve, reject, or flag |
| `/api/v1/human-review/bulk-approve` | POST | Bulk approve list of IDs |
| `/api/v1/human-review/bulk-reject` | POST | Bulk reject list of IDs |
| `/api/v1/human-review/summary` | GET | Queue summary stats per run |

### Exports & Notion

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/export/{id}` | POST | Generate CSV, JSON, PDF for a run |
| `/api/v1/exports/download/{export_job_id}` | GET | Download a generated export file |
| `/api/v1/notion-sync/prepare/{id}` | POST | Stage run data for Notion |
| `/api/v1/notion-sync/run/{id}` | POST | Execute Notion sync (idempotent) |

### Intelligence & Trending

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/intelligence/run/{id}/insights` | GET | Retrieve all agent insights for a run |
| `/api/v1/intelligence/llm-cache-stats` | GET | LLM response cache hit/miss/hit-rate |
| `/api/v1/trending/top` | GET | Top trending pain points across all runs |
| `/api/v1/trending/run/{run_id}` | GET | Fingerprints for a specific run |
| `/api/v1/trending/run/{run_id}/update` | POST | Trigger fingerprint update for a run |
| `/api/v1/topic-modeling/{run_id}` | GET | Full topic analysis (ML + seed clusters) |
| `/api/v1/topic-modeling/{run_id}/clusters` | GET | Lightweight cluster summary |
| `/api/v1/agent-orchestration/run/{run_id}` | POST | Run Anthropic 5-agent pipeline on all evidence |

### Auth & Organizations

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/auth/register` | POST | Create a user account |
| `/api/v1/auth/login` | POST | OAuth2 form login, returns JWT |
| `/api/v1/auth/refresh` | POST | Refresh access token |
| `/api/v1/auth/me` | GET | Get current user |
| `/api/v1/organizations` | POST | Create organization (with generated API key) |
| `/api/v1/organizations/{slug}` | GET | Get organization details |
| `/api/v1/organizations/{slug}/rotate-api-key` | POST | Rotate the organization's API key |

---

## Database Schema

| Table | Purpose |
|---|---|
| `scrape_runs` | One record per analysis session (brand, source_name, status, session_notes, organization_id, archived_at) |
| `raw_evidence` | Every scraped post, review, comment with normalisation + multilingual fields |
| `run_events` | SSE pipeline events streamed to the frontend |
| `agent_insights` | All AI agent outputs (pain label, cluster, root cause, priority, action, analysis_mode) |
| `retrieval_documents` | 128-dim pgvector embeddings for semantic search |
| `human_review_queue` | Items pending review with reviewer_decision, reviewer_notes, priority |
| `notion_sync_jobs` | Notion sync job tracking per approved queue item (idempotent sync_key) |
| `export_jobs` | Export generation jobs with file_path, file_size, row_count |
| `system_state` | Key-value store for platform configuration state |
| `pain_point_fingerprints` | Cross-run SHA256-keyed pain point recurrence + weekly trend buckets |
| `users` | User accounts with role (admin/analyst/viewer), bcrypt password hash |
| `organizations` | Multi-tenant orgs with plan, max_runs_per_month, rotatable API key |

Run all migrations:

```bash
cd apps/api && alembic upgrade head
```

Reset all data while preserving schema:

```bash
docker compose exec -T postgres psql -U postgres -d repi_db -c "
TRUNCATE TABLE
  agent_insights, export_jobs, human_review_queue,
  notion_sync_jobs, pain_point_fingerprints, retrieval_documents,
  run_events, raw_evidence, scrape_runs
RESTART IDENTITY CASCADE;
"
```

---

## Background Tasks

ARQ + Redis processes 7 async task types (defined in `apps/api/app/workers/tasks.py`):

| Task | Triggered by |
|---|---|
| `task_execute_scrape` | `POST /api/v1/scrape-execution/{run_id}` |
| `task_normalize_run` | Normalize pipeline step |
| `task_multilingual_run` | Multilingual pipeline step |
| `task_intelligence_run` | Intelligence step (also triggers trending + topic modeling) |
| `task_retrieval_index` | Build search library step |
| `task_generate_review_queue` | Create review list step |
| `task_generate_exports` | Create files step |

Worker settings: 10 concurrent jobs, 300s timeout, 1hr result retention.

**Running the worker (development):**

```bash
cd apps/api && python -m arq app.workers.tasks.WorkerSettings
```

Without the worker, all pipeline endpoints execute synchronously (suitable for dev). With the worker, endpoints enqueue tasks and return a job ID immediately; the frontend SSE stream shows progress as the task runs.

---

## Authentication

JWT-based authentication via `python-jose` + `passlib[bcrypt]`.

**Dev mode bypass**: when `JWT_SECRET_KEY` equals the default placeholder in `.env.example`, a synthetic admin user is returned for all `get_current_user` dependencies — no token required. This keeps local development frictionless.

**Production mode**: set a real `JWT_SECRET_KEY`. Sensitive endpoints (`POST /api/v1/runs`, `POST /api/v1/scrape-execution/{id}`) require a valid Bearer token.

**Optional API key auth** (simpler for internal tooling): set `API_KEY_ENABLED=true` and `API_KEY_SECRET=your-key`. Send `X-API-Key: your-key` header. Exempts `/health`, `/docs`, `/`, `/openapi.json`, `/redoc`.

---

## Observability

**Prometheus metrics**: automatically collected via `prometheus-fastapi-instrumentator`. Exposed at `GET /metrics`. Start with `--profile monitoring` to scrape into Prometheus and visualize in Grafana.

**Sentry error tracking**: set `SENTRY_DSN` in `.env`. Integrations: FastAPI + SQLAlchemy. 10% traces sample rate (configurable via `SENTRY_TRACES_SAMPLE_RATE`).

**Per-run log files**: `apps/api/logs/run_{id}.log` captures the full pipeline lifecycle for every scrape run. Log file path appended to `orchestrator_notes` in the run record. Captures: raw count per source, kept/skipped_positive/skipped_empty per step, normalization errors, intelligence item-by-item labels, review queue generation.

**Run diagnostics API**: `GET /api/v1/orchestrator/run/{id}/diagnostics` returns stage timeline, latest event, readiness snapshot, failure snapshot, stale-run flag.

**Observability overview**: `GET /api/v1/orchestrator/observability` returns active queue count, stale run count, recent failed runs, review backlog, run status distribution.

---

## Exports

Three formats generated per run via the **Create Files** pipeline step:

| Format | Contents |
|---|---|
| **CSV** | All pain points with journey stage, taxonomy cluster, priority score, root cause, action recommendation, source |
| **JSON** | Full structured output: raw evidence metadata, agent insights, trending fingerprints, session notes |
| **PDF** | Executive summary with ReportLab: session metadata, pain point listing, priority breakdown |

Files saved to `apps/api/generated_exports/` (gitignored). Download via `GET /api/v1/exports/download/{export_job_id}` (serves `FileResponse` with correct MIME type and `Content-Disposition`).

The **Exports** panel in the console shows completed exports with ↓ Download buttons, pending jobs, and empty state. Download links use the absolute FastAPI base URL (`NEXT_PUBLIC_API_BASE_URL`), not relative Next.js routes.

---

## Notion Integration

Push approved pain points to a Notion database in two pipeline steps:

**Prepare Notion Sync** — stages approved queue items as Notion sync jobs. Each job gets a stable `sync_key` (SHA256 of run_id + insight_id) for idempotency.

**Run Notion Sync** — writes each pain point as a Notion page with: Title (pain label), Status, Priority (High/Medium/Low), Brand, Source, Root Cause, Action, and Decision properties. Existing synced pages are never re-created.

Configure in `.env`:

```env
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=your-database-id
NOTION_ENABLE_REAL_SYNC=true
```

Without `NOTION_ENABLE_REAL_SYNC=true`, the sync jobs are staged but no actual Notion API calls are made (safe dry-run default).

---

## Trending & Fingerprinting

The `pain_point_fingerprints` table tracks pain points across runs using SHA256 fingerprint keys derived from `"label:cluster"`.

**`TrendingService.update_fingerprints_for_run(db, run_id)`** — called automatically after every intelligence step. For each `AgentInsight` in the run, increments `recurrence_count` and the current week bucket (`count_week_0`).

**`rotate_weekly_counts(db)`** — designed to run on a weekly schedule. Shifts `week_0 → week_1 → week_2 → week_3`. Items absent from the latest week show a declining trend.

**`trend_direction`** — computed as: `rising` (week_0 > avg(weeks 1–3)), `declining` (week_0 < avg/2), `stable` otherwise.

**`GET /api/v1/trending/top`** — returns top N pain points by recurrence count with trend direction. Useful for identifying chronic, persistent issues vs one-off complaints.

---

## Topic Modeling

The `TopicModelingService` uses a 4-tier fallback strategy (best available method wins):

**Tier 1 — HDBSCAN semantic clustering** (requires `sentence-transformers` + `hdbscan`): True BERTopic-style — embeds all evidence texts, clusters in embedding space, extracts TF-IDF keywords per cluster. Best quality, requires ML libraries.

**Tier 2 — NMF matrix factorization** (requires `scikit-learn`): TF-IDF vectorizer → NMF decomposition. Extracts N latent topics with top-10 keywords per topic.

**Tier 3 — LDA topic extraction** (requires `scikit-learn`): Count vectorizer → LDA online learning. Alternative to NMF.

**Tier 4 — Seed-keyword clusters** (always available, no dependencies): 8 predefined real estate pain clusters scored by keyword overlap frequency. Shannon entropy diversity score computed across clusters.

Topic modeling is triggered automatically at the end of the intelligence step when `TOPIC_MODELING_ENABLED=true` (default). Results accessible via `GET /api/v1/topic-modeling/{run_id}`.

---

## Multi-Tenant Organizations

The `organizations` table enables workspace isolation for team deployments:

- Each organization has a `slug`, `name`, `plan` (free/starter/pro/enterprise), `max_runs_per_month`, and a rotatable `api_key`.
- `scrape_runs` and `users` both carry an `organization_id` FK.
- `POST /api/v1/organizations` creates an org with a randomly generated API key.
- `POST /api/v1/organizations/{slug}/rotate-api-key` issues a new key (previous key immediately invalid).

Multi-tenancy enforcement (query scoping by organization) is a V4 scope item — the schema foundation is fully in place.

---

## Changelog

### Step 38 — Scraper Accuracy Fixes + Docker Hardening + YouTube Sentiment Fix

- **Square Yards app IDs corrected**: Play Store `com.sq.yrd.squareyards`, App Store `1093755061`. `BRAND_APPSTORE_SLUGS` dict + `_get_appstore_slug()` added to both scrapers.
- **iOS App Store upgraded to `app-store-scraper` library** (Tier A): proper library with `store.review(how_many=100)`. iTunes RSS kept as automatic Tier B fallback.
- **`app-store-scraper` installed with `--no-deps`** in Dockerfile to avoid `requests==2.23.0` vs `sentry-sdk` `urllib3` conflict.
- **YouTube sentiment filter fixed**: `NEGATIVE_SIGNAL_KEYWORDS` expanded with ~20 new terms (experience, comparison, Hindi transliterations). Search query broadened from exact-match quoted brand to complaint-focused unquoted query.
- **Detailed logging** added to `review_sites.py`: raw count per SDK fetch + kept/skipped breakdown after sentiment filter.
- **Dockerfile multi-stage build hardened**: `python:3.11` (full) as builder eliminates broken apt-get calls; `COPY app/ ./app/` added for setuptools wheel build; `curl` healthcheck replaced with Python `urllib`.
- **Next.js standalone output**: added `output: "standalone"` to `next.config.ts` — fixes `docker compose build web` failing with `/app/.next/standalone: not found`.

### Step 37 — Codebase Audit + Bug Fixes + Hardening

- **ARQ tasks**: 4 wrong method names fixed (`execute()` → `execute_run()`, etc.). Trending + topic modeling auto-triggered after intelligence step.
- **X scraper relabeled** to HackerNews Algolia — honest sourcing, real `news.ycombinator.com` URLs, `tech_discussions_hn` platform tag.
- **Item caps removed**: `scraper_max_items_per_source` raised 10 → 500. Review sites expanded to 500 Play / 5 RSS pages.
- **Pagination**: `GET /api/v1/runs` and `GET /api/v1/evidence` return `{items, total, limit, offset}` with proper `model_validate()` serialization.
- **Data archiving**: `archived_at` column, archive/unarchive endpoints, frontend Archive button.
- **React error boundaries**: 12 panels each wrapped in `ErrorBoundary` — crash isolation per panel.
- **JWT auth on sensitive routes**: `POST /api/v1/runs` and `POST /api/v1/scrape-execution/{id}` require auth in prod mode.
- **Context post-filtering** for app store scrapers.
- **Runtime fixes**: nested `<button>` hydration crash, context double-parsing bug, silent exception eating in app_reviews, per-run log file directory path, duplicate log lines, YouTube `maxResults` capped at 50, HN query broadened, pre-filter logging across all scrapers.

### Step 36 — Context-Aware Scraping

- Research context chips (6 prebuilt: Website & Mobile App, Listings, Projects & Builders, Sales Process & Agents, Post-Sales Process, Complaints & Escalations) + custom text field in Run Setup.
- `context_utils.py` with `CONTEXT_KEYWORD_MAP` and `extract_context_keywords()`.
- All 5 scrapers updated to accept and thread `context: str | None`.
- `Promise.allSettled` in workspace refresh prevents one failing endpoint from blanking the whole console.
- Migration 0017 final idempotency fix using `sqlalchemy.dialects.postgresql.ENUM` with `create_type=False`.

### Step 35 — Scraper Hardening, Review Queue UX, Multi-Source Sessions

- Dual-store app reviews (Google Play + Apple) with sentiment filter, 100 reviews each.
- Review Queue: Pending/Approved/Rejected/All tabs with live counts, pagination, Select All, bulk actions.
- Multi-source sessions: platform checkboxes, `ScrapeExecutionService` fan-out.
- Session Notes: dedicated `session_notes` column (migration 0020), never overwritten by pipeline.
- Hydration mismatch fix: relative timestamps computed client-side only.
- Export download 404 fix: absolute backend URL for download links.
- Alembic chain repair: migration 0018 corrected `down_revision`.

### Steps 29–34 — Production-Grade Tier

- **Step 29**: ARQ + Redis background tasks, JWT auth, rate limiting, DB pooling.
- **Step 30**: Docker multi-stage builds, GitHub Actions CI/CD, Prometheus, Sentry, circuit breakers, sentence-transformers embeddings.
- **Step 31**: LLM TTL caching, gpt-4o-mini cost optimization, cross-run pain point trending, multi-tenant org model.
- **Step 32**: BERTopic-style topic modeling (NMF/LDA/HDBSCAN graceful degradation), 5-agent Anthropic tool_use orchestration.
- **Step 33**: TypeScript build fixes, export downloads UI, Pain Points persona panel, Reddit PRAW 3-tier scraper, Active Sessions compact redesign.
- **Step 34**: Evidence Explorer panel, Retrieval Search panel, Notion sync steps reinstated, source ID corrections (99acres, MagicBricks, Housing, NoBroker), PullPush.io Tier 2 for Reddit, YouTube verified channel IDs.

### Steps 0–28 — V1 / V2 Foundation

Steps 0–16 delivered the complete V1 feature set: monorepo, FastAPI skeleton, PostgreSQL foundation, all data models and migrations, scraper registry, streaming pipeline, cleaning/normalisation, multilingual, multi-agent intelligence, pgvector retrieval, human review workflow, Notion integration, export system, and final hardening guardrails.

Steps 17–28 delivered the V2 scope: live source connectors for all 5 sources, real export generation, real Notion API integration, embedding-backed retrieval, LLM-assisted hybrid intelligence, review console backend, pipeline observability and diagnostics, full frontend product console, background job queue, dark-to-light theme migration, and comprehensive backend hardening.

---

## Contributing

Active development branch: `main` (with feature branches per step)

```bash
# Create a feature branch
git checkout -b feat/your-change

# Make changes and commit
git add apps/api/... apps/web/...
git commit -m "feat: description of change"

# Push and open a PR
git push origin feat/your-change
```

**Linting:**

```bash
# Python (from apps/api/)
ruff check .

# TypeScript (from apps/web/)
npm run lint
npm run build          # full production build check
npx tsc --noEmit       # type-check only
```

**Tests:**

```bash
# Python tests (from apps/api/)
source .venv/bin/activate
pytest tests/ -v
```

**Known open items (lower priority):**

- P1: Real semantic embeddings via sentence-transformers (graceful degradation is in place; upgrade when ML deps available)
- P8: IndicNLP / lightweight Hinglish translation for true bilingual processing
- P11: React Context / Zustand to replace prop-drilling in WorkspaceShell
