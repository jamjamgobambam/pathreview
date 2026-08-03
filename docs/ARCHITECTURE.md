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

`HybridRetriever.retrieve()` (`rag/retriever/hybrid.py`) blends two independent signals into a single relevance score per chunk:

- **Vector similarity** — cosine similarity from the ChromaDB vector store, converted from distance as `1 / (1 + distance)` (`rag/retriever/vector_store.py`).
- **BM25 keyword** — a sparse keyword relevance score from `rank_bm25` (`rag/retriever/keyword_search.py`).

Because the two raw scores live on different scales (cosine similarity is already ~0–1, BM25 is unbounded), each score set is first **normalized to 0–1 by dividing every score by the maximum score in that set**. The normalized scores are then combined with a weighted sum:

```
blended = vector_weight * norm(vector_score) + keyword_weight * norm(keyword_score)
```

**Current defaults** (`HybridRetriever.__init__`): `vector_weight = 0.7`, `keyword_weight = 0.3`, so vector similarity dominates while keyword matching provides a lexical boost.

After blending, results are **filtered by `min_score`** (default `0.3`), **sorted by blended score descending**, and truncated to the top **`max_chunks`** (default `10`).

**Worked example.** Suppose a chunk is returned by both searchers, and across the two result sets the maximum vector score is `0.80` and the maximum BM25 score is `8.0`:

| Signal | Raw score | Set max | Normalized | Weight | Contribution |
|--------|-----------|---------|------------|--------|--------------|
| Vector | 0.60 | 0.80 | 0.60 / 0.80 = 0.75 | 0.7 | 0.525 |
| Keyword | 4.0 | 8.0 | 4.0 / 8.0 = 0.50 | 0.3 | 0.150 |

The blended score is `0.525 + 0.150 = 0.675`, which is above the `0.3` threshold, so the chunk is kept and ranked by that value.

**Edge cases the code handles:**
- **Found by only one searcher** — the missing side scores `0`, and the chunk still contributes through the weighted sum (e.g. a vector-only hit scores at most `0.7`).
- **Empty result sets / zero max** — normalization guards against divide-by-zero by falling back to `0`, so an empty side contributes nothing rather than erroring.
- **Everything filtered out** — if no chunk meets `min_score`, `retrieve()` returns an empty list.

> These values (`0.7` / `0.3` weights, `0.3` `min_score`) are the current defaults in `rag/retriever/hybrid.py`; they are constructor/method arguments and can be overridden per call.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
