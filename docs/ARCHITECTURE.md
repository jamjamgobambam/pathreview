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

`HybridRetriever.retrieve` (`rag/retriever/hybrid.py`) combines two independent signals for each candidate chunk:

- **Vector score** — cosine similarity from `VectorStore.query`.
- **Keyword score** — BM25 relevance from `KeywordSearcher.search`.

The two signals live on different scales, so each is normalized to 0–1 before blending by dividing every score in a result set by the maximum score in that same result set. This normalization is per query, not a fixed global scale — a vector score of `1.0` means "the best vector match for this query," not an absolute similarity threshold. If a result set is empty, its max defaults to `1.0` to avoid a divide-by-zero.

A chunk found by only one retrieval method (say, a strong keyword match with no vector hit) is not excluded — the missing side's score defaults to `0`, so the chunk is still scored using only the signal it has.

The normalized scores are blended as:

```
score = vector_weight * vector_score + keyword_weight * keyword_score
```

`vector_weight` and `keyword_weight` are constructor parameters of `HybridRetriever`, not hardcoded constants, defaulting to `vector_weight=0.7` and `keyword_weight=0.3`. No call site in this codebase currently constructs `HybridRetriever` with overrides, so these defaults are also the only values in effect today — but they remain tunable per instance.

Chunks with a blended score below `min_score` (default `0.3`) are dropped before the remaining results are sorted and truncated to `max_chunks`. A short or unusual query can legitimately push every candidate below `min_score`, returning zero chunks — that's expected threshold behavior, not a bug.

**Worked example:** a chunk with normalized `vector_score=0.8` and `keyword_score=0.4` blends to `0.7 * 0.8 + 0.3 * 0.4 = 0.68`, which clears the `0.3` `min_score` cutoff.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
