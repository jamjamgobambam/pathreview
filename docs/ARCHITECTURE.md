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

#### Hybrid retrieval scoring

Ranking is implemented in `HybridRetriever` (`rag/retriever/hybrid.py`). Vector hits come from `rag/retriever/vector_store.py`; keyword hits come from BM25 in `rag/retriever/keyword_search.py`. For each candidate chunk id that appears in either channel, PathReview builds a **blended** score as follows.

**1. Per-channel max-normalization** (relative to the current candidate set, not a global constant):

```text
vector_norm  = raw_vector_score / max(raw_vector_scores_in_candidate_set)
keyword_norm = raw_bm25_score   / max(raw_bm25_scores_in_candidate_set)
```

If a chunk is missing from one channel, that channel’s normalized score is treated as `0.0`. Empty candidate sets use a safe default max of `1.0` so division does not blow up.

**2. Weighted blend** (constructor defaults):

| Parameter | Default | Meaning |
|---|---|---|
| `vector_weight` | **0.7** | Weight on normalized vector similarity |
| `keyword_weight` | **0.3** | Weight on normalized BM25 keyword score |

```text
blended = vector_weight * vector_norm + keyword_weight * keyword_norm
```

With the defaults this is:

```text
blended = 0.7 * vector_norm + 0.3 * keyword_norm
```

Weights are configurable on `HybridRetriever`; the table above documents the defaults shipped in code.

**3. Filter, sort, truncate**

- Drop candidates with `blended < min_score` (default **`min_score=0.3`**; equality is kept via `>=`).
- Sort remaining results by blended score descending.
- Return the top `max_chunks` (default `10`).

Each returned row includes `score` (blended), plus the normalized `vector_score` and `keyword_score` for debugging.

**Worked example**

Suppose the candidate set’s max raw vector score is `1.0` and max raw BM25 score is `10.0`. For one chunk with raw vector `0.9` and raw BM25 `6.0`:

```text
vector_norm  = 0.9 / 1.0 = 0.90
keyword_norm = 6.0 / 10.0 = 0.60
blended      = 0.7 * 0.90 + 0.3 * 0.60 = 0.63 + 0.18 = 0.81
```

`0.81 >= 0.3`, so the chunk is kept and can rank above weaker blends. A chunk with blended `0.25` would be filtered out by the default threshold.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
