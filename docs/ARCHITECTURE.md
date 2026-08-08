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

`HybridRetriever.retrieve()` (`rag/retriever/hybrid.py`) runs vector similarity search and BM25 keyword search independently, then blends their scores into a single ranking:

1. **Normalize.** Each side's raw scores are min-max normalized against the maximum score *within that search's own result set* (not a global maximum across queries):
   - `vector_norm = vector_score / max(vector_scores)`
   - `keyword_norm = bm25_score / max(bm25_scores)`

   A chunk returned by only one of the two searches gets a `0` for the missing side — its score is not filled in from the other method.

2. **Blend.** The normalized scores are combined with a weighted sum:

   ```
   score = vector_weight * vector_norm + keyword_weight * keyword_norm
   ```

   Defaults are `vector_weight=0.7`, `keyword_weight=0.3`, favoring semantic (vector) matches while letting a strong keyword match act as a tiebreaker or boost.

3. **Filter and rank.** Chunks scoring below `min_score` (default `0.3`) are dropped; the rest are sorted by blended score, and the top `max_chunks` are returned.

Because normalization is per-query and per-result-set, the blended score is a relative ranking signal, not an absolute measure of chunk quality — the same raw vector or BM25 score can normalize differently across queries depending on what else was retrieved.

**Worked example:**

| Chunk | Raw vector score | Raw BM25 score | vector_norm | keyword_norm | Blended score (0.7 / 0.3) |
|-------|------------------|-----------------|-------------|---------------|----------------------------|
| A     | 0.82             | 4.1             | 0.82/0.82 = 1.00 | 4.1/6.5 = 0.63 | 0.7(1.00) + 0.3(0.63) = 0.889 |
| B     | 0.75             | 6.5             | 0.75/0.82 = 0.91 | 6.5/6.5 = 1.00 | 0.7(0.91) + 0.3(1.00) = 0.940 |

Chunk B outranks Chunk A despite a lower raw vector score, because its stronger keyword match is enough to overcome the 0.7/0.3 weighting.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
