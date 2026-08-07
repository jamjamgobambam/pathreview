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

`HybridRetriever.retrieve()` (in `rag/retriever/hybrid.py`) blends two independent signals into a single ranking score for each candidate chunk:

```text
   blended_score = (vector_weight * normalized_vector_score) + (keyword_weight * normalized_keyword_score)
```



**Default weights** are `vector_weight=0.7` and `keyword_weight=0.3`. These are constructor parameters on `HybridRetriever`, not hardcoded constants, so they can be tuned per-instance if a different balance between semantic and lexical matching is desired.

**Normalization** happens per result set, not globally: each vector score is divided by the maximum vector score within that query's vector results, and each keyword (BM25) score is divided by the maximum keyword score within that query's keyword results. This means the same raw score can normalize very differently between queries, since it's always relative to what else was retrieved for that specific query, not a fixed 0-1 scale.

**Result set union:** a chunk only needs to appear in one of the two result sets (vector or keyword) to receive a blended score. If a chunk is missing from one side, that side's contribution is treated as 0 rather than excluding the chunk entirely.

**Worked example** (default weights):

| Chunk | Vector score (raw) | Keyword/BM25 (raw) | Normalized vector | Normalized keyword | Blended (0.7v + 0.3k) |
|-------|--------------------|--------------------|--------------------|--------------------|------------------------|
| A | 0.9 | - | 1.000 | 0 | 0.700 |
| B | 0.6 | 5.0 | 0.667 | 1.000 | 0.767 |
| C | 0.3 | 2.0 | 0.333 | 0.400 | 0.353 |
| D | - | 1.0 | 0 | 0.200 | 0.060 |

With a min_score threshold of 0.3, chunk D is filtered out. The final ranking is B, A, C - note that B outranks A here even though A had the higher raw vector score, because B's strong keyword match pushes its blended score above A's.

This example is verified by the test suite in `tests/unit/test_hybrid_retriever.py`, which asserts these exact blended values.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)