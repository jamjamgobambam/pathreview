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
### Hybrid retrieval scoring

The hybrid retriever combines vector similarity results with BM25 keyword
results. Because the two retrieval methods produce scores on different scales,
each set of scores is normalized independently before the scores are combined.

For each chunk, the normalized scores are calculated as:

```text
normalized_vector_score = vector_score / maximum_vector_score
normalized_keyword_score = bm25_score / maximum_bm25_score
```

The final blended score is:

```text
blended_score =
    (vector_weight * normalized_vector_score)
    + (keyword_weight * normalized_keyword_score)
```

The current default weights are:

- Vector similarity: `0.7`
- BM25 keyword relevance: `0.3`

For example, suppose a chunk has a normalized vector score of `0.8` and a
normalized keyword score of `0.6`. Its blended score is:

```text
(0.7 * 0.8) + (0.3 * 0.6) = 0.74
```

A chunk that appears in only one result set receives a score of `0` from the
other retrieval method. Results with a blended score below the minimum
threshold are removed. The current default minimum score is `0.3`; scores equal
to the threshold are retained. The remaining chunks are sorted from highest to
lowest blended score, and only the requested maximum number of chunks is
returned.

Vector similarity scores originate in `rag/retriever/vector_store.py`, where
ChromaDB distance is converted using `1 / (1 + distance)`. BM25 scores originate
in `rag/retriever/keyword_search.py`. The normalization, weighting, filtering,
and ranking logic is implemented in `rag/retriever/hybrid.py`.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
