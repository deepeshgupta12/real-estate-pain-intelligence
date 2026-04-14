# Real Estate Pain Point Intelligence Platform

A full-stack AI-powered platform that scrapes public sources across the Indian real estate market, extracts and clusters pain points using a multi-agent LLM pipeline, and surfaces actionable insights through a polished console UI.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [Running the Platform](#running-the-platform)
- [Pipeline Walkthrough](#pipeline-walkthrough)
- [API Reference](#api-reference)
- [Data Sources](#data-sources)
- [Intelligence Pipeline](#intelligence-pipeline)
- [Frontend Console](#frontend-console)
- [Notion Integration](#notion-integration)
- [Exports](#exports)
- [Database Schema](#database-schema)
- [Contributing](#contributing)

---

## Overview

The platform answers a single question for real estate brands operating in India:

> **What are customers actually complaining about — and why?**

It does this end-to-end: scrape → clean → analyse → cluster → prioritise → act.

A single run targets one brand (e.g. "Square Yards", "NoBroker", "MagicBricks") across all configured public sources. The multi-agent pipeline then extracts pain points, clusters them into a taxonomy, generates root-cause hypotheses, benchmarks against competitors, and produces prioritised action recommendations — all surfaced in a streaming console UI.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js 16 Frontend                  │
│   Console UI  ·  Evidence Explorer  ·  Review Queue     │
│   Semantic Search  ·  Exports  ·  Notion Sync           │
└────────────────────────┬────────────────────────────────┘
                         │ REST + SSE streaming
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend (v0.2)                 │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │  Scrapers   │  │  Pipeline   │  │  AI Agents     │  │
│  │  Reddit     │  │  Orchestr.  │  │  Pain Extract  │  │
│  │  YouTube    │  │  Normalise  │  │  Taxonomy      │  │
│  │  App Stores │  │  Multilang  │  │  Root Cause    │  │
│  │  X/Twitter  │  │  Retrieval  │  │  Competitor    │  │
│  │  Review     │  │  Indexing   │  │  Prioritise    │  │
│  └─────────────┘  └─────────────┘  └────────────────┘  │
└──────┬───────────────────────────────────┬──────────────┘
       │                                   │
┌──────▼──────┐                   ┌────────▼────────┐
│ PostgreSQL  │                   │   OpenAI API    │
│ + pgvector  │                   │   gpt-4o-mini   │
│ port 5460   │                   └─────────────────┘
└─────────────┘
```

---

## Features

### Data Collection
- **Multi-source scraping** across Reddit, YouTube, Google Play / App Store, X (Twitter), and Indian review sites
- **Tiered fallback** per scraper: primary source → secondary source → stub (stubs only if explicitly enabled)
- **Live data by default** (`SCRAPER_FAIL_OPEN_TO_STUB=false`)
- Reddit via PRAW (official API) → PullPush.io archive → RSS fallback
- YouTube via YouTube Data API v3 → yt-dlp fallback
- App reviews: up to 100 most-recent per store from **both** Google Play (`google-play-scraper` SDK) and Apple App Store (iTunes RSS pages 1 + 2)
- Each review/post tagged with `store_platform` ("google_play" / "ios_app_store") and `platform` ("reddit" / "youtube" / "x_twitter") in metadata
- **Sentiment filtering** — purely positive content (rating ≥ 4, no negative signal keywords) is skipped at collection time across all scrapers
- **Pain point summary** — first meaningful sentence extracted per item and stored in metadata for quick-scan display

### Intelligence Pipeline
- **Cleaning & normalisation** — deduplication, language detection, content-type tagging
- **Multilingual support** — Hinglish / Hindi transliteration handling
- **Pain point extraction** — LLM identifies specific grievances per post
- **Taxonomy & clustering** — groups pain points into a structured hierarchy
- **Root-cause hypothesis** — LLM reasons about systemic causes
- **Competitor benchmarking** — cross-brand signal comparison
- **Prioritisation** — frequency × severity × trend scoring
- **Action recommendations** — ranked, actionable next steps

### Console UI
- **Streaming pipeline progress** — real-time SSE updates per step
- **Evidence Explorer** — browse every raw post/review collected, filter by source and type, full-text search
- **Semantic Search** — natural language search across the vector index
- **Human Review Queue** — filter by Pending / Approved / Rejected / All with live counts; bulk approve/reject with Select All; paginated (20 items/page)
- **Run Diagnostics** — health checks, stale run detection, recent failures
- **Pipeline Actions** — 9-step orchestrated pipeline with one-click execution
- **Exports** — download results as CSV, JSON, or PDF
- **Notion Sync** — push pain points directly into a Notion database

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4 |
| Backend | FastAPI 0.115, Python 3.10+, Uvicorn |
| Database | PostgreSQL 16 + pgvector extension |
| ORM / Migrations | SQLAlchemy 2.0, Alembic |
| AI / LLM | OpenAI `gpt-4o-mini` via `openai` SDK |
| Vector embeddings | pgvector (cosine similarity, 64-dim) |
| Background jobs | ARQ + Redis |
| Scraping | PRAW, google-play-scraper, yt-dlp, httpx |
| Observability | Prometheus, Sentry SDK |
| Rate limiting | SlowAPI |

---

## Project Structure

```
real-estate-pain-intelligence/
├── apps/
│   ├── api/                          # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/v1/               # REST endpoints
│   │   │   │   ├── runs.py           # Scrape run CRUD
│   │   │   │   ├── evidence.py       # Raw evidence retrieval
│   │   │   │   ├── orchestrator.py   # Pipeline orchestration
│   │   │   │   ├── intelligence.py   # AI agent endpoints
│   │   │   │   ├── retrieval.py      # Semantic search
│   │   │   │   ├── human_review.py   # Review queue
│   │   │   │   ├── notion_sync.py    # Notion integration
│   │   │   │   ├── export.py         # CSV / JSON / PDF export
│   │   │   │   └── ...
│   │   │   ├── scrapers/
│   │   │   │   └── sources/
│   │   │   │       ├── reddit.py     # PRAW → PullPush → RSS
│   │   │   │       ├── youtube.py    # Data API v3 → yt-dlp
│   │   │   │       ├── app_reviews.py# Google Play → Apple RSS
│   │   │   │       ├── x_posts.py    # X / Twitter scraper
│   │   │   │       └── review_sites.py
│   │   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── services/             # Business logic layer
│   │   │   ├── integrations/         # Notion, OpenAI clients
│   │   │   ├── workers/              # ARQ background workers
│   │   │   └── main.py
│   │   ├── alembic/                  # Database migrations
│   │   ├── docker-compose.yml        # PostgreSQL + pgvector container
│   │   ├── pyproject.toml
│   │   └── .env.example
│   └── web/                          # Next.js frontend
│       └── src/
│           ├── app/                  # App Router pages
│           ├── components/
│           │   └── console/          # All console panel components
│           │       ├── workspace-shell.tsx
│           │       ├── run-setup-panel.tsx
│           │       ├── pipeline-actions-panel.tsx
│           │       ├── pipeline-progress-panel.tsx
│           │       ├── evidence-explorer-panel.tsx
│           │       ├── retrieval-search-panel.tsx
│           │       ├── pain-points-panel.tsx
│           │       ├── review-console-panel.tsx
│           │       ├── exports-panel.tsx
│           │       └── ...
│           └── lib/
│               └── api.ts            # Typed API client
└── docs/
    └── implementation-tracker.md
```

---

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Docker Desktop** (for PostgreSQL + pgvector)
- **OpenAI API key** (for LLM analysis steps)
- **YouTube Data API v3 key** (free — for YouTube scraping)
- **Reddit API credentials** (optional — for PRAW live scraping)

---

## Local Setup

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

This starts PostgreSQL 16 with the pgvector extension on port `5460`.

### 3. Set up the backend

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -e ".[dev]"

# Copy and configure environment variables
cp .env.example .env
# Edit .env — at minimum set OPENAI_API_KEY and YOUTUBE_DATA_API_KEY

# Run database migrations
alembic upgrade head
```

### 4. Set up the frontend

```bash
cd apps/web
npm install
```

---

## Environment Variables

Copy `apps/api/.env.example` to `apps/api/.env` and configure the following:

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string — default matches Docker setup |
| `OPENAI_API_KEY` | Yes | OpenAI key for LLM analysis |
| `INTELLIGENCE_OPENAI_MODEL` | No | Defaults to `gpt-4o-mini` |
| `YOUTUBE_DATA_API_KEY` | Yes | YouTube Data API v3 key — free 10k units/day |
| `REDDIT_CLIENT_ID` | No | Reddit app client ID (PRAW) |
| `REDDIT_CLIENT_SECRET` | No | Reddit app client secret |
| `REDDIT_API_ENABLED` | No | `true` to enable PRAW. Defaults to `false` (uses PullPush.io) |
| `NOTION_API_KEY` | No | Notion integration token |
| `NOTION_DATABASE_ID` | No | Target Notion database ID |
| `SCRAPER_FAIL_OPEN_TO_STUB` | No | `false` (default) = live data only. `true` = allow stubs on failure |
| `SCRAPER_MAX_ITEMS_PER_SOURCE` | No | Max items per source per run. Default: `10` |

### Getting a YouTube Data API v3 key (free, ~2 minutes)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a project
2. Enable **YouTube Data API v3**
3. Go to Credentials → Create Credentials → API Key
4. Paste it into `.env` as `YOUTUBE_DATA_API_KEY`

Free quota: 10,000 units/day ≈ ~100 search requests.

### Getting Reddit API credentials (optional)

1. Go to [reddit.com/prefs/apps](https://reddit.com/prefs/apps)
2. Create app → choose "script" type
3. Copy `client_id` and `client_secret` into `.env`
4. Set `REDDIT_API_ENABLED=true`

Without PRAW credentials, the Reddit scraper falls back to PullPush.io (Pushshift-compatible archive, no auth required).

---

## Running the Platform

### Start the backend

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

### Start the frontend

```bash
cd apps/web
npm run dev
```

Console available at `http://localhost:3000`

---

## Pipeline Walkthrough

A full analysis run consists of 9 steps executed in order from the Pipeline Actions panel:

| Step | Action | What it does |
|---|---|---|
| 1 | **Scrape** | Collects raw posts, reviews, and comments from all configured sources |
| 2 | **Clean & Normalise** | Deduplicates, detects language, tags content type |
| 3 | **Multilingual** | Handles Hinglish / Hindi transliteration |
| 4 | **Run Intelligence** | LLM extracts pain points, builds taxonomy, root-cause hypotheses, competitor benchmarks, and priority rankings |
| 5 | **Build Search Library** | Embeds all evidence into the pgvector index for semantic search |
| 6 | **Human Review** | Opens the review queue — approve, reject, or flag extracted pain points |
| 7 | **Prepare Notion Sync** | Stages approved pain points for Notion export |
| 8 | **Run Notion Sync** | Pushes staged data to your Notion database |
| 9 | **Create Exports** | Generates CSV, JSON, and PDF report files |

Each step streams real-time progress events to the console via Server-Sent Events (SSE).

---

## API Reference

Full interactive docs at `http://localhost:8000/docs` when the backend is running.

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/v1/runs` | POST | Create a new scrape run |
| `/api/v1/runs` | GET | List all runs |
| `/api/v1/evidence` | GET | Browse raw evidence (`run_id`, `source_name`, `content_type`, `limit`) |
| `/api/v1/orchestrator/run/{id}/full` | POST | Execute the full pipeline for a run |
| `/api/v1/orchestrator/run/{id}/stream` | GET | SSE stream of pipeline events |
| `/api/v1/retrieval/search` | POST | Semantic search across the vector index |
| `/api/v1/human-review/queue` | GET | Fetch the review queue |
| `/api/v1/human-review/{id}` | PATCH | Approve, reject, or flag a queue item |
| `/api/v1/notion-sync/prepare/{id}` | POST | Stage run data for Notion export |
| `/api/v1/notion-sync/run/{id}` | POST | Execute Notion sync |
| `/api/v1/export/{id}` | POST | Generate exports (CSV, JSON, PDF) for a run |

---

## Data Sources

| Source | Scraper | Tier 1 | Tier 2 | Notes |
|---|---|---|---|---|
| **Reddit** | `reddit.py` | PRAW (official API) | PullPush.io archive | PullPush requires no credentials |
| **YouTube** | `youtube.py` | YouTube Data API v3 | yt-dlp | API key required for Tier 1 |
| **App Reviews** | `app_reviews.py` | Google Play SDK | Apple App Store RSS | No credentials needed |
| **X / Twitter** | `x_posts.py` | Public search | Curated stubs | Rate-limited by platform |
| **Review Sites** | `review_sites.py` | Google Play ratings | Apple ratings | Aggregated review scores |

Scrapers use a tiered architecture — if a higher tier fails (blocked, rate-limited, no credentials), the next tier is automatically tried. Stubs are only used as a last resort when `SCRAPER_FAIL_OPEN_TO_STUB=true`.

---

## Intelligence Pipeline

The AI analysis pipeline runs via OpenAI `gpt-4o-mini` in an orchestrated sequence:

**Pain Point Extraction** — identifies specific, discrete complaints from each piece of raw evidence.

**Taxonomy & Clustering** — groups extracted pain points into a structured hierarchy: theme → category → sub-issue.

**Root Cause Hypothesis** — reasons about the underlying systemic causes for each cluster.

**Competitor Benchmarking** — compares pain point patterns across different brands in the corpus.

**Prioritisation** — scores each cluster by frequency, severity, and recency trend.

**Action Recommendations** — generates ranked, concrete next steps for each priority cluster.

All agent outputs are stored as `AgentInsight` records and surfaced in the Pain Points panel.

---

## Frontend Console

The console is a single-page workspace at `http://localhost:3000` with a left sidebar for navigation:

| Panel | Description |
|---|---|
| **Run Setup** | Configure brand name, target source, and create a new run |
| **Pipeline Actions** | One-click buttons for each of the 9 pipeline steps |
| **Pipeline Progress** | Live SSE stream showing step-by-step progress |
| **Current Run** | Summary stats for the active run |
| **Pain Points** | Extracted and clustered pain points with priority scores |
| **Evidence Explorer** | Browse raw collected posts, filter by source/type, full-text search |
| **Semantic Search** | Natural language search across the vector index |
| **Review Console** | Filter queue by Pending / Approved / Rejected / All; live counts update instantly after each action; bulk approve/reject with Select All; 20-items-per-page pagination |
| **Run Diagnostics** | System health, stale runs, recent failures |
| **Exports** | Download CSV, JSON, or PDF for the current run |

---

## Notion Integration

Push approved pain points to a Notion database in two steps from the Pipeline Actions panel:

1. **Prepare Notion Sync** — stages the run's approved insights
2. **Run Notion Sync** — writes each pain point as a Notion page with Status, Priority, Brand, Source, and Decision properties

Configure in `.env`:

```env
NOTION_API_KEY=secret_...
NOTION_DATABASE_ID=your-database-id
NOTION_ENABLE_REAL_SYNC=true
```

Get your integration token at [notion.so/my-integrations](https://www.notion.so/my-integrations). Make sure to share your Notion database with the integration before syncing.

---

## Exports

Three formats are generated per run via the **Create Exports** pipeline step:

| Format | Contents |
|---|---|
| **CSV** | All pain points with scores, sources, and recommendations |
| **JSON** | Full structured output including taxonomy, root causes, and agent metadata |
| **PDF** | Formatted report with executive summary, priority matrix, and action plan |

Exports are saved to `apps/api/generated_exports/` and downloadable from the **Exports** panel in the console. Download links call the FastAPI backend directly (`http://localhost:8000/api/v1/exports/download/:id`) — configure `NEXT_PUBLIC_API_BASE_URL` if the API runs on a different host or port.

---

## Database Schema

| Table | Purpose |
|---|---|
| `scrape_runs` | One record per analysis run (brand, source, status, timestamps) |
| `raw_evidence` | Every scraped post, review, comment, or video |
| `run_events` | SSE pipeline events streamed to the frontend |
| `agent_insights` | All AI agent outputs (pain points, taxonomy, recommendations) |
| `retrieval_documents` | pgvector embeddings for semantic search |
| `human_review_queue` | Items pending human review with approve/reject/flag status |
| `notion_sync_jobs` | Notion sync job tracking per run |
| `export_jobs` | Export generation jobs and file paths |
| `system_state` | Key-value store for platform-wide configuration state |

Run migrations any time models change:

```bash
cd apps/api
alembic upgrade head
```

To reset all data while preserving the schema:

```bash
docker compose exec -T postgres psql -U postgres -d repi_db -c "
TRUNCATE TABLE
  agent_insights, export_jobs, human_review_queue,
  notion_sync_jobs, retrieval_documents, run_events,
  raw_evidence, scrape_runs
RESTART IDENTITY CASCADE;
"
```

---

## Changelog

### Step 35 — Scraper hardening, Review Queue UX, FE cleanup (`feat/step-35-enhancements`)

**Scraper improvements (all sources)**
- Dual-store app reviews: up to 100 most-recent reviews fetched from both Google Play and Apple App Store per run
- Sentiment filtering applied across Reddit, YouTube, X, App Reviews, and Review Sites — purely positive signals (rating ≥ 4, no negative keywords) are discarded at collection time
- Each item tagged with `platform` and `store_platform` metadata for per-source breakdown in the UI
- `pain_point_summary` (first sentence of content) extracted and stored per item

**Review Queue**
- Added Pending / Approved / Rejected / All filter tabs with live counts driven from local React state — counts update instantly after every approve/reject action without a backend re-fetch
- Default view is **Pending** so you land immediately on actionable items
- Empty state "🎉 All caught up — no pending reviews!" when pending tab is empty
- Colour-coded item cards (green = approved, red = rejected, blue = selected)
- Bulk actions toolbar and inline approve/reject buttons only shown on Pending tab
- 20-items-per-page pagination with numbered page buttons; pagination resets on filter change

**Pain Points panel**
- Per-source summary chip row restored below the panel header, showing count per source with colour-coded badges (Reddit, YouTube, App Reviews, Review Sites, X)

**Dashboard**
- Removed redundant APPLICATION / ENVIRONMENT / API PREFIX / CURRENT BUILD meta cards from the overview header

**Bug fixes**
- **Hydration mismatch** in Activity Log panel: relative timestamps ("32m ago") now computed client-side only via `useEffect`, eliminating the SSR/client text mismatch that caused React's hydration error
- **Export download 404**: download links now use the full FastAPI backend URL instead of a relative path that was incorrectly routed to Next.js

---

## Contributing

Active development branch: `feat/step-35-enhancements`

```bash
# Create a feature branch off main
git checkout -b feat/your-feature

# Make changes and commit
git add .
git commit -m "feat: your change description"

# Push and open a PR against main
git push origin feat/your-feature
```

**Linting:**
- Python: `ruff check .` from `apps/api/`
- TypeScript: `npm run lint` from `apps/web/`
