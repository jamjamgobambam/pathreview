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

`HybridRetriever` (`rag/retriever/hybrid.py`) runs vector search and BM25 keyword search independently, then blends their scores into a single ranking score per chunk.

Because vector similarity and BM25 scores live on different scales, each is first **normalized to `[0, 1]` by dividing by the maximum score in its own result set**:

```
norm_vector  = vector_score / max(vector_scores)
norm_keyword = bm25_score   / max(bm25_scores)
```

The two normalized scores are then combined with a **weighted sum**:

```
blended_score = vector_weight * norm_vector + keyword_weight * norm_keyword
```

The default weights are **`vector_weight = 0.7`** and **`keyword_weight = 0.3`**, favoring semantic similarity over lexical matching. Both are constructor parameters on `HybridRetriever`, so they can be tuned per deployment.

Chunks are unioned across both result sets, so a chunk found by only one method still gets scored — the **missing signal simply contributes `0`** for its component (e.g. a chunk with no keyword hit scores `0.7 * norm_vector + 0.3 * 0`). If a result set is empty its max is treated as `1.0` to avoid division by zero.

Finally, chunks scoring below `min_score` (default `0.3`) are dropped, the rest are sorted by `blended_score` descending, and the top `max_chunks` (default `10`) are returned.

**Worked example** — with default weights, a chunk that ranks top on vector search (`norm_vector = 1.0`) but has no keyword match (`norm_keyword = 0.0`) scores `0.7 * 1.0 + 0.3 * 0.0 = 0.70`, while a chunk that is a moderate match on both (`norm_vector = 0.6`, `norm_keyword = 0.8`) scores `0.7 * 0.6 + 0.3 * 0.8 = 0.66`. The vector-only chunk ranks higher, reflecting the 0.7 weighting toward semantic relevance.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
