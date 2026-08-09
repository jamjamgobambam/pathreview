# Architecture Overview

PathReview is a multi-service application with five major subsystems. This document describes how they fit together.

## High-Level Data Flow

```
User Input (GitHub username, resume PDF, repo URLs)
    │
    ▼
┌─────────────────────┐
│  API Layer (FastAPI) │ ← Authentication, validation, rate limiting
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Ingestion Pipeline  │ ← Parse documents, chunk, embed, store
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Agent Orchestrator  │ ← Plan analysis, execute tools, manage state
│  ┌───────────────┐  │
│  │ GitHub Tool    │  │
│  │ Skill Extract  │  │
│  │ README Scorer  │  │
│  │ Market Analyze │  │
│  │ Tech Detector  │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  RAG System          │ ← Retrieve context, generate feedback, evaluate
│  (Hybrid Retrieval   │
│   + LLM Generation)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Safety Layer        │ ← Bias check, content filter, PII scrub
└──────────┬──────────┘
           │
           ▼
      Review Output
```

## Subsystem Details

### API Layer (`api/`)
FastAPI application serving REST endpoints. Handles authentication (JWT), request validation (Pydantic), rate limiting, and CORS. Routes delegate to service layer in `core/services/`.

### Ingestion Pipeline (`ingestion/`)
Processes user-submitted documents into vector embeddings. Parsers implement `BaseParser` and extract structured text. Chunkers split text for embedding. The pipeline orchestrates: parse → chunk → embed → store.

### Agent System (`agent/`)
A plan-execute orchestrator that coordinates multiple analysis tools. Each tool implements `BaseTool` with `name`, `description`, and `execute()`. The orchestrator builds a plan based on available profile data, executes tools with retry and timeout policies, and synthesizes results.

### RAG System (`rag/`)
Hybrid retrieval (vector similarity + BM25 keyword) fetches relevant context from the user's ingested documents. The generator uses prompt templates to produce structured, evidence-based feedback. The evaluator scores retrieval relevance and generation faithfulness.

#### Hybrid Retrieval Scoring

`HybridRetriever.retrieve` ([hybrid.py](../rag/retriever/hybrid.py)) blends vector similarity and BM25 keyword scores into a single ranking score:

```
blended_score = vector_weight * normalized_vector_score + keyword_weight * normalized_keyword_score
```

Each side is normalized to 0–1 by dividing by the max score in its own result set (`normalized_vector_score = vector_score / max(vector_scores)`, and likewise for the keyword side using `bm25_score`). If a chunk is returned by only one of the two searches, the other side's score is treated as `0` rather than excluded — it's still blended, not dropped. If a result set's max score is `0`, that side's normalized score is `0` rather than a divide-by-zero.

Default weights: `vector_weight=0.7`, `keyword_weight=0.3` — vector similarity dominates the ranking, keyword match is a secondary signal.

**Worked example** — a query returns three candidate chunks:

| Chunk | Vector score | Normalized vector | BM25 score | Normalized keyword | Blended (0.7 / 0.3) |
|---|---|---|---|---|---|
| A (both) | 0.90 | 0.90/0.90 = 1.00 | 8.0 | 8.0/8.0 = 1.00 | 0.7×1.00 + 0.3×1.00 = **1.00** |
| B (vector only) | 0.60 | 0.60/0.90 = 0.67 | — | 0 | 0.7×0.67 + 0.3×0 = **0.47** |
| C (keyword only) | — | 0 | 4.0 | 4.0/8.0 = 0.50 | 0.7×0 + 0.3×0.50 = **0.15** |

Results are filtered by `min_score` (default `0.3`) before being sorted and truncated to `max_chunks`. In this example, chunk C falls below the default threshold and is dropped — a keyword-only match needs a much stronger relative BM25 score to clear the bar than a vector-only match needs on the vector side, since `keyword_weight` is smaller. This is why keyword-only matches are disadvantaged by default.

**Known limitation:** `_get_all_chunks` fetches every chunk in the collection but its result is never passed into `keyword_searcher.index()` before `.search()` is called, so keyword scores may be empty at runtime unless the searcher was indexed elsewhere beforehand. This is a behavior gap, not a documentation gap — tracked separately from this scoring writeup.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
