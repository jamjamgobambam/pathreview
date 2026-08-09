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

`HybridRetriever` (`rag/retriever/hybrid.py`) combines two independent retrievers into a single ranked list. It is the source of truth for the weights and thresholds below; the defaults quoted here may drift, so treat the code as authoritative.

**Pipeline.** For a query, both retrievers each fetch `max_chunks * 2` candidates:

1. **Vector search** (`rag/retriever/vector_store.py`) queries ChromaDB and converts each distance to a similarity score, `score = 1 / (1 + distance)`, so higher is more similar.
2. **Keyword search** (`rag/retriever/keyword_search.py`) runs BM25 (`BM25Okapi`) over whitespace-tokenized, lowercased text and returns an unbounded `bm25_score` per chunk.

The two candidate sets are unioned by chunk id, each score is normalized, blended, filtered, and the top `max_chunks` are returned.

**Normalization.** Each retriever's scores are divided by the maximum score *within its own result set*, mapping them to `0–1`:

```
vector_norm  = vector_score  / max(all vector_scores)
keyword_norm = bm25_score    / max(all bm25_scores)
```

This is max-normalization (divide by max), not min-max normalization — the minimum is not subtracted, so the lowest-scoring surviving chunk is not forced to `0`. If a result set is empty its max defaults to `1.0`, avoiding division by zero.

**Blending formula.** Normalized scores are combined with fixed weights:

```
blended = vector_weight * vector_norm + keyword_weight * keyword_norm
```

Defaults are `vector_weight = 0.7` and `keyword_weight = 0.3` (constructor arguments of `HybridRetriever`). A chunk found by only one retriever contributes `0` for the signal it is missing, so a keyword-only chunk can score at most `keyword_weight` (0.3) and a vector-only chunk at most `vector_weight` (0.7).

**Filtering and ranking.** Chunks with `blended < min_score` are dropped (`min_score = 0.3` by default), the survivors are sorted by `blended` descending, and the first `max_chunks` are returned. If every chunk falls below `min_score` the result list is empty; if fewer than `max_chunks` survive, all survivors are returned without padding.

**Worked example.** A query returns chunk A (vector only), chunk B (both), and chunk C (keyword only). Suppose the raw scores are:

| Chunk | raw vector | raw bm25 | vector_norm | keyword_norm | blended (0.7 / 0.3) | kept (≥ 0.3)? |
|---|---|---|---|---|---|---|
| A | 0.80 | — | 0.80 / 0.80 = 1.00 | 0.00 | 0.7·1.00 + 0.3·0.00 = **0.700** | yes |
| B | 0.60 | 4.0 | 0.60 / 0.80 = 0.75 | 4.0 / 5.0 = 0.80 | 0.7·0.75 + 0.3·0.80 = **0.765** | yes |
| C | — | 5.0 | 0.00 | 5.0 / 5.0 = 1.00 | 0.7·0.00 + 0.3·1.00 = **0.300** | yes (== cutoff) |

Final ranking: **B (0.765) > A (0.700) > C (0.300)**. Chunk C survives only because it exactly meets the `0.3` cutoff; had its blended score been any lower it would have been dropped.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
