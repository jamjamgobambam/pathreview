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

`HybridRetriever` (`rag/retriever/hybrid.py`) blends two signals because neither alone is sufficient: vector similarity catches paraphrases and related concepts but misses exact tokens, while BM25 catches literal terms (framework names, acronyms) but misses semantic matches. Each query runs both searches, requesting `max_chunks * 2` candidates from each side, and the two candidate sets are merged by chunk ID.

The two raw scores are not comparable — vector scores come back as `1 / (1 + distance)` and land in `(0, 1]`, while BM25 scores are unbounded and depend on corpus statistics. So each side is **max-normalized** against its own result set before blending: every raw score is divided by the largest raw score in that set, which puts both signals on a 0–1 scale and makes the top hit on each side exactly `1.0`. If a side returns no results (or an all-zero maximum), its normalized contribution is `0` rather than a division by zero.

The normalized scores are then combined linearly:

```
score = vector_weight * normalized_vector_score + keyword_weight * normalized_keyword_score

where  normalized_vector_score  = raw_vector_score  / max(raw_vector_scores)
       normalized_keyword_score = raw_bm25_score    / max(raw_bm25_scores)
```

A chunk that appears in only one candidate set still gets a blended score — the missing side contributes `0`. Chunks scoring below `min_score` are dropped, the rest are sorted by blended score descending, and the top `max_chunks` are returned. Each returned chunk carries its `vector_score` and `keyword_score` components alongside the blended `score`, which is useful when debugging why a chunk ranked where it did.

| Parameter | Default | Set in | Meaning |
|---|---|---|---|
| `vector_weight` | `0.7` | `HybridRetriever.__init__` | Weight applied to the normalized vector score |
| `keyword_weight` | `0.3` | `HybridRetriever.__init__` | Weight applied to the normalized BM25 score |
| `max_chunks` | `10` | `retrieve()` | Chunks returned; each side is queried for `2x` this many candidates |
| `min_score` | `0.3` | `retrieve()` | Chunks with a blended score below this are dropped |

The defaults favor semantic similarity over keyword matching roughly 2:1, on the assumption that a reviewer's query ("what testing experience does this candidate have?") rarely uses the same wording as the source document.

**Worked example.** A query returns three chunks from vector search and three from BM25 (`C1` and `C2` appear on both sides). The raw maxima are `0.60` for vector and `8.0` for BM25:

| Chunk | Raw vector | Raw BM25 | Normalized vector | Normalized keyword | Blended score |
|---|---|---|---|---|---|
| `C1` | 0.60 | 2.0 | 0.60 / 0.60 = **1.00** | 2.0 / 8.0 = **0.25** | 0.7(1.00) + 0.3(0.25) = **0.775** |
| `C2` | 0.42 | 8.0 | 0.42 / 0.60 = **0.70** | 8.0 / 8.0 = **1.00** | 0.7(0.70) + 0.3(1.00) = **0.790** |
| `C3` | 0.30 | — | 0.30 / 0.60 = **0.50** | absent → **0** | 0.7(0.50) + 0.3(0) = **0.350** |
| `C4` | — | 4.0 | absent → **0** | 4.0 / 8.0 = **0.50** | 0.7(0) + 0.3(0.50) = **0.150** |

`C4` scores `0.150`, below the `0.3` cutoff, so it is dropped. The final ranking is `C2` (0.790), `C1` (0.775), `C3` (0.350). Note that `C2` outranks `C1` even though `C1` was the single best vector hit — a strong keyword match is enough to overcome a moderate vector deficit, which is the whole point of blending.

Two consequences worth knowing when tuning:

- **Normalization is relative to the current result set**, not global. A chunk's score describes how it compares to the other candidates for *this* query, so blended scores are not comparable across queries, and `min_score` behaves as a relative threshold rather than an absolute confidence level.
- **The cutoff is inclusive.** The filter is `score >= min_score`, so a chunk scoring exactly `0.3` is kept.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
