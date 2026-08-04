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

#### Hybrid retrieval scoring formula

`HybridRetriever.retrieve()` (`rag/retriever/hybrid.py`) combines two independent retrieval methods into one ranked list:

1. **Vector search** (`VectorStore.query()`) queries a ChromaDB collection configured for cosine space and converts the returned cosine distance to a similarity score: `similarity = max(0.0, 1 - distance)`. Negative similarities (distance > 1, meaning the query and chunk embeddings point in substantially different directions) are clamped to `0.0`.
2. **Keyword search** (`KeywordSearcher.search()`) scores chunks with BM25 (`rank_bm25.BM25Okapi`) over whitespace-tokenized, lowercased text, producing a raw `bm25_score`.

Each side is fetched independently (`max_chunks * 2` candidates per side), then combined:

1. **Normalize.** Each result set is scaled by its own maximum: `norm_vector = vector_score / max(vector_scores)`, `norm_keyword = bm25_score / max(bm25_scores)`. A chunk that only appears in one result set gets `0.0` for the other side.
2. **Blend.** `blended_score = vector_weight * norm_vector + keyword_weight * norm_keyword`, with defaults `vector_weight=0.7`, `keyword_weight=0.3` (configurable per `HybridRetriever` instance — these are unvalidated defaults, not empirically tuned).
3. **Filter and rank.** Chunks with `blended_score < min_score` (default `0.3`) are dropped; the rest are sorted descending and truncated to `max_chunks`.

**Worked example:** a chunk has cosine distance `0.35` to the query → `similarity = 1 - 0.35 = 0.65`. The top vector result in this query's batch scored `0.80`, so `norm_vector = 0.65 / 0.80 = 0.8125`. The same chunk has a raw BM25 score of `4.2`, versus a batch max of `6.0`, so `norm_keyword = 4.2 / 6.0 = 0.7`. Blended: `0.7 * 0.8125 + 0.3 * 0.7 = 0.779`, well above the `0.3` cutoff, so the chunk is kept and ranked by that score against the rest of the candidates.

If a collection or query returns no results on one side, that side's max defaults to `1.0` to avoid a divide-by-zero — it does not fabricate matches, it just means every candidate scores `0.0` on that side.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
