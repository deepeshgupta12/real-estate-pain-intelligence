# Architecture Overview

## Product
Real Estate Pain Point Intelligence Platform

## Objective
Convert public user pain points related to Indian real-estate platforms into actionable product recommendations for Square Yards.

## High-level system
1. Multi-source scraping
2. Raw evidence storage
3. Cleaning and normalization
4. Journey-stage mapping
5. Pain-point extraction
6. Taxonomy and clustering
7. Root-cause hypothesis generation
8. Competitor benchmarking
9. Prioritization
10. Action recommendation
11. Human review
12. Notion sync
13. Export layer
14. Dashboard and run monitoring

## Initial technical foundation
- Backend: FastAPI
- Frontend: Next.js
- Database: PostgreSQL
- Queue/streaming: Redis in later steps
- LLM support: OpenAI with hybrid rules
- Vector layer: planned in later phase