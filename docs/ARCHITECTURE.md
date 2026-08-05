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

`HybridRetriever.retrieve` (`rag/retriever/hybrid.py`) combines two independent searches into a single ranked list:

- **Vector search** returns a similarity `score` in `(0, 1]`, computed from ChromaDB's euclidean distance as `1 / (1 + distance)` (`rag/retriever/vector_store.py`). Higher is more similar.
- **Keyword search** returns a `bm25_score` from `rank_bm25`'s `BM25Okapi.get_scores()`. This score is **unbounded** — it depends on term frequency, document length, and corpus statistics, and routinely exceeds `1.0`.

Because these two scores live on different scales, each is normalized before blending:

```
normalized_score = raw_score / max(raw_score across the current result set)
```

This is a **max-of-result-set** normalization, not a global or fixed-range normalization — the divisor is the highest score returned for *this query*, not a constant learned in advance. If the max score in a result set is `0`, the normalized score is defined as `0` (guards against division by zero).

The normalized scores are then blended with configurable weights, defaulting to `vector_weight=0.7` and `keyword_weight=0.3`:

```
blended_score = (vector_weight * normalized_vector_score) + (keyword_weight * normalized_keyword_score)
```

**Chunks found by only one method** are still included: the missing side's score is treated as `0` rather than excluding the chunk. For example, a chunk that only the keyword search surfaced gets `vector_score = 0` and is ranked purely on its normalized BM25 contribution.

After blending, results below `min_score` (default `0.3`) are filtered out, and the remainder is sorted descending by `blended_score` and truncated to `max_chunks`. It's possible for every candidate to fall below `min_score`, in which case retrieval returns an empty list.

**Worked example:** Suppose a query returns two vector matches with raw scores `0.87` and `0.74` (max = `0.87`), and two keyword matches with raw BM25 scores `5.2` and `1.1` (max = `5.2`). A chunk that appears in both result sets with vector score `0.74` and BM25 score `1.1` normalizes to:

```
normalized_vector  = 0.74 / 0.87 = 0.851
normalized_keyword = 1.1  / 5.2  = 0.212

blended_score = (0.7 * 0.851) + (0.3 * 0.212) = 0.596 + 0.064 = 0.660
```

A chunk found only by keyword search with BM25 score `5.2` (the set max) normalizes to `1.0` on the keyword side and `0` on the vector side:

```
blended_score = (0.7 * 0) + (0.3 * 1.0) = 0.300
```

That second chunk only survives the default `min_score=0.3` filter by an exact margin — a useful illustration of how a keyword-only match can still rank, but needs a strong relative BM25 score to clear the threshold given the 0.7/0.3 weighting favors vector similarity.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
