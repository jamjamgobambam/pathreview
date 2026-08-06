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
<!-- TODO #36: hybrid scoring formula undocumented here. See rag/hybrid.py for
     normalization logic (score / max_score per method), weighted sum
     (vector_weight=0.7, bm25_weight=0.3), threshold filter, and top-k sort. -->

The RAG system combines semantic vector retrieval with BM25 keyword retrieval. Vector retrieval identifies chunks whose embeddings are semantically similar to the query, while BM25 prioritizes chunks containing relevant query terms.

The retriever requests up to twice the desired number of results from each retrieval method. Because vector similarity and BM25 use different scoring scales, their raw scores are normalized independently before they are combined. For each retrieval method, a chunk's score is divided by the highest score returned by that method:

```text
normalized_vector_score = vector_score / highest_vector_score
normalized_keyword_score = bm25_score / highest_bm25_score
```

The final hybrid score is calculated as a weighted sum:

```text
hybrid_score =
    (vector_weight * normalized_vector_score)
    + (keyword_weight * normalized_keyword_score)
```

The default weights are:

```text
vector_weight = 0.7
keyword_weight = 0.3
```
These weights are set when the retriever is initialized and apply to all queries made by that instance.

These defaults give semantic similarity more influence while still allowing exact keyword matches to improve a chunk's ranking. If a chunk appears in only one retrieval result set, its normalized score for the missing retrieval method is `0`.

For example, suppose the highest vector score in the result set is `0.90` and the highest BM25 score is `8.0`. A candidate chunk has a vector score of `0.72` and a BM25 score of `6.0`:

```text
normalized_vector_score = 0.72 / 0.90 = 0.80
normalized_keyword_score = 6.0 / 8.0 = 0.75

hybrid_score = (0.7 * 0.80) + (0.3 * 0.75)
             = 0.56 + 0.225
             = 0.785
```

The chunk's final hybrid score is `0.785`. After all candidate chunks are scored, the retriever removes chunks below the configured minimum score, sorts the remaining chunks in descending order, and returns the highest-ranking results. By default, retrieval returns up to 10 chunks and applies a minimum hybrid score of `0.3`.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
