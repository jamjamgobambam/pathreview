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

`HybridRetriever` (`rag/retriever/hybrid.py`) blends two independent signals into a single relevance score for each candidate chunk:

- **Vector score** — cosine similarity from `VectorStore.query()` (`rag/retriever/vector_store.py`).
- **Keyword score** — a raw BM25 score from `KeywordSearcher.search()` (`rag/retriever/keyword_search.py`).

Because the two scores live on different scales, each is first **normalized against the maximum score in its own result set** for the query (divide by max; guarded against divide-by-zero, defaulting to `0` when a result set is empty). The normalized scores are then combined with fixed weights:

```
blended_score = vector_weight * (vector_score / max(vector_scores))
              + keyword_weight * (keyword_score / max(keyword_scores))
```

The default weights, set in the `HybridRetriever` constructor, favor the semantic signal:

| Weight | Default | Meaning |
|---|---|---|
| `vector_weight` | `0.7` | Contribution of vector similarity |
| `keyword_weight` | `0.3` | Contribution of BM25 keyword overlap |

A chunk returned by only one of the two searches still gets a blended score — the missing side simply contributes `0`.

**Worked example.** Suppose a query returns two candidate chunks:

| Chunk | Raw vector score | Raw BM25 score |
|---|---|---|
| A | 0.90 (max) | 4.0 |
| B | 0.60 | 8.0 (max) |

Normalizing each column by its max gives vector scores `1.00` / `0.67` and keyword scores `0.50` / `1.00`. Applying the default `0.7` / `0.3` weights:

- Chunk A: `0.7 * 1.00 + 0.3 * 0.50 = 0.85`
- Chunk B: `0.7 * 0.67 + 0.3 * 1.00 = 0.77`

Chunk A ranks first even though Chunk B's keyword match was stronger, because the default weighting favors semantic similarity.

After blending, `HybridRetriever.retrieve()` drops any chunk below `min_score` (default `0.3`) and returns at most `max_chunks` (default `10`) results — so the final list can be shorter than `max_chunks`, or empty, if nothing clears the threshold. The weights are constructor arguments, not global constants, so callers can retune the vector/keyword balance per use case without touching the blending logic itself.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
