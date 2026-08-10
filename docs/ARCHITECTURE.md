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

Retrieval combines a **dense** signal (semantic vector similarity) and a **sparse** signal (BM25 keyword overlap) into a single ranked list. The two signals are computed independently, normalized to a common range, then blended with fixed weights. Implemented in `rag/retriever/`.

**1. Vector similarity (`vector_store.py`).** Collections are created with `metadata={"hnsw:space": "cosine"}`, so ChromaDB ranks by **cosine distance** `d ∈ [0, 2]` (`0` = identical direction, `1` = orthogonal, `2` = opposite). Each distance is converted to a bounded similarity:

```
vector_similarity = 1 / (1 + d)          # d = cosine distance, similarity ∈ (0, 1]
```

This mapping is monotonic (smaller distance → higher score), so it preserves ChromaDB's ranking while giving a positive score usable in the blend. Because the metric is cosine, similarity depends on embedding *direction*, not magnitude.

> Note: ChromaDB's default space is `l2` (which actually returns *squared* Euclidean distance); this collection overrides it to cosine, which is why the conversion above operates on cosine distance rather than a Euclidean one.

**2. Keyword score (`keyword_search.py`).** `BM25Okapi` (from `rank_bm25`) scores each chunk against the query over whitespace-lowercased tokens. Raw BM25 scores are unbounded and corpus-dependent.

**3. Per-signal max-normalization (`hybrid.py`).** Each signal is divided by the maximum score within its own result set, mapping both to roughly `[0, 1]` so neither signal's raw scale dominates the blend. Normalization guards against divide-by-zero (a signal with no results contributes `0`).

**4. Weighted blend (`hybrid.py`).** Scores are combined per chunk over the *union* of the two result sets:

```
blended_score = vector_weight · vector_norm + keyword_weight · keyword_norm
              = 0.7 · vector_norm + 0.3 · keyword_norm   # defaults
```

A chunk found by only one signal simply scores `0` on the other and still contributes via its weighted term. **Heuristic:** vector similarity is weighted higher (`0.7` vs `0.3`) because semantic matching generalizes across paraphrase and vocabulary mismatch, while BM25 mainly rewards exact term overlap; keyword search is kept as an additive signal that boosts chunks containing the query's literal terms. The weights are constructor arguments to `HybridRetriever` (`vector_weight`, `keyword_weight`) and can be tuned.

**5. Threshold and ranking (`hybrid.py`).** Blended results below `min_score` (default `0.3`) are dropped, the rest are sorted by score descending, and the top `max_chunks` (default `10`) are returned. If every chunk falls below `min_score`, retrieval legitimately returns an empty list.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
