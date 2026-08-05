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

`HybridRetriever` (`rag/retriever/hybrid.py`) ranks chunks by blending the two search methods:

1. Vector search and BM25 keyword search each return their own candidate set, over-fetching to twice the requested chunk count.

2. Each method's scores are normalized to a 0 to 1 range by dividing by that method's highest score in the candidate set.

3. Every chunk found by either method receives a blended score:

   ```
   score = vector_weight * vector_norm + keyword_weight * keyword_norm
   ```

   The default weights are `vector_weight=0.7` and `keyword_weight=0.3`, set as constructor defaults on `HybridRetriever`. A chunk returned by only one method scores 0 on the other side, so it can still rank well if that one method scores it highly.

4. Chunks with a blended score below `min_score` (default 0.3) are dropped. The rest are sorted by blended score, highest first, and truncated to the requested chunk count.

**Example with default weights:**

| Chunk | Raw vector | Normalized vector | Raw BM25 | Normalized BM25 | Blended score |
|-------|-----------|-------------------|----------|-----------------|---------------|
| A | 0.82 | 0.82 / 0.82 = 1.0 | not returned | 0 | 0.7 × 1.0 + 0.3 × 0 = 0.70 |
| B | 0.41 | 0.41 / 0.82 = 0.5 | 6.0 | 6.0 / 6.0 = 1.0 | 0.7 × 0.5 + 0.3 × 1.0 = 0.65 |
| C | not returned | 0 | 3.0 | 3.0 / 6.0 = 0.5 | 0.7 × 0 + 0.3 × 0.5 = 0.15 |

With `min_score=0.3`, chunks A and B are returned in that order and chunk C is dropped. Note that A ranks first without any keyword match: the vector side carries the larger default weight.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
