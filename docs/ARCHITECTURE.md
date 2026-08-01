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

`HybridRetriever.retrieve()` (in `rag/retriever/hybrid.py`) ranks chunks by blending two signals: **semantic** (vector) similarity and **lexical** (BM25 keyword) relevance. Neither signal alone is reliable — vector search can miss exact identifiers (a specific library or framework name), while keyword search misses paraphrases — so their normalized scores are combined into a single blended score.

**The formula**

```
blended_score = vector_weight · (vector_similarity / max_vector_similarity)
              + keyword_weight · (bm25_score / max_bm25_score)
```

**Default weights** (constructor arguments of `HybridRetriever`):

| Weight | Default | Meaning |
|---|---|---|
| `vector_weight` | **0.7** | Contribution of semantic similarity |
| `keyword_weight` | **0.3** | Contribution of BM25 keyword relevance |

The defaults favor semantic similarity 70/30. They are plain constructor arguments and are **not** validated to sum to 1 — passing weights that sum to something other than 1 rescales the blended score and shifts how the `min_score` threshold (below) behaves.

**How the two scores are normalized**

The vector and BM25 scores live on different, incomparable scales, so each is **max-normalized to the 0–1 range** before blending — every raw score is divided by the largest score of its own kind in the current candidate set:

- **Vector similarity.** The vector store returns a similarity derived from the raw distance as `similarity = 1 / (1 + distance)` (`rag/retriever/vector_store.py`). Each result's similarity is then divided by the maximum similarity in the vector candidate set.
- **BM25 keyword.** The keyword searcher returns raw, unbounded BM25 scores (`rag/retriever/keyword_search.py`). Each is divided by the maximum BM25 score in the keyword candidate set.

Because normalization is relative to the current query's candidates, the top result of each kind always normalizes to exactly `1.0`. Scores are therefore comparable **within** a single query's ranking, but not **across** different queries.

Retrieval then keeps only chunks whose blended score is at least `min_score` (default **0.3**), sorts by blended score descending, and returns the top `max_chunks` (default **10**).

**Worked example**

Suppose a query returns these candidates (a chunk may be found by one or both methods):

| Chunk | Vector similarity | BM25 score |
|---|---|---|
| A | 0.90 | 8.0 |
| B | 0.60 | — (not in keyword results) |
| C | 0.45 | 4.0 |
| D | — (not in vector results) | 2.0 |

Normalize each column by its maximum (`max_vector = 0.90`, `max_bm25 = 8.0`); a chunk missing from one method contributes `0` for that method. Then blend with the default `0.7 / 0.3` weights:

| Chunk | Norm. vector | Norm. keyword | Blended = 0.7·v + 0.3·k | Result |
|---|---|---|---|---|
| A | 1.000 | 1.000 | **1.000** | keep |
| C | 0.500 | 0.500 | **0.500** | keep |
| B | 0.667 | 0.000 | **0.467** | keep |
| D | 0.000 | 0.250 | **0.075** | dropped (< `min_score` 0.3) |

Final ranking: **A → C → B**. Chunk C, matched by both methods, outranks chunk B, which is strong on vectors alone; chunk D is filtered out because its single weak keyword match cannot clear the `0.3` threshold.

**Notes and edge cases**

- **Union of candidates.** The candidate pool is the union of both methods' results; a chunk found by only one method scores `0` for the other (see chunks B and D above).
- **`min_score` interacts with the weights.** With the defaults, a keyword-only chunk peaks at `0.3 × 1.0 = 0.3` — only the single top keyword match can reach the threshold — while a vector-only chunk needs a normalized vector score of at least `0.3 / 0.7 ≈ 0.43` to survive.
- **Empty / zero-score sets.** If a method returns no results (or all-zero scores), its normalization denominator is guarded so the blend degrades gracefully to the other method instead of dividing by zero.
- **Relative normalization.** Because scores are normalized per query, a blended score measures *relative* rank within one query, not an absolute confidence level.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
