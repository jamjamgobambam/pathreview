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

The RAG subsystem combines dense vector similarity search with sparse BM25 keyword search using the `HybridRetriever` class (`rag/retriever/hybrid.py`). The retrieval and score blending process follows four key steps:

1. **Candidate Fetching & Pool Oversampling**:
   - For a given query, the retriever fetches candidate document chunks from both search engines using an oversampling factor of `2 * max_chunks` (defaulting to 20 candidate chunks per search method when `max_chunks = 10`).

2. **Max Score Normalization**:
   - Raw scores from vector similarity (`vector_score`) and BM25 keyword search (`bm25_score`) operate on different scales. Each candidate set's raw scores are normalized to a `[0.0, 1.0]` range by dividing by the maximum score in that candidate set:

     ```text
     vector_score_norm = vector_score / vector_scores_max
     keyword_score_norm = bm25_score / keyword_scores_max
     ```

   - *Zero-Division Safeguard*: If the maximum score in a candidate set is zero (`max_score <= 0`) or if no candidate results are returned, the normalized score defaults to `0.0`.

3. **Weighted Score Blending**:
   - The normalized scores are combined using a weighted linear sum to produce a single `blended_score`:

     ```text
     blended_score = (vector_weight * vector_score_norm) + (keyword_weight * keyword_score_norm)
     ```

   - Default weight parameters:
     - **Vector Similarity Weight (`vector_weight`)**: `0.7`
     - **BM25 Keyword Weight (`keyword_weight`)**: `0.3`

4. **Filtering & Ranking**:
   - **Minimum Score Threshold**: Candidate chunks with `blended_score < min_score` (default `0.3`) are filtered out.
   - **Top-K Selection**: Remaining chunks are sorted in descending order by `blended_score`, and the top `max_chunks` (default `10`) are returned as the final retrieved context.

#### Step-by-Step Worked Example

Consider a query evaluated against three candidate document chunks (`chunk-A`, `chunk-B`, and `chunk-C`) using default weights (`vector_weight = 0.7`, `keyword_weight = 0.3`, `min_score = 0.3`):

##### 1. Raw Scores Fetched
- **`chunk-A`**: Raw Vector Score = `0.80`, Raw BM25 Score = `12.0`
- **`chunk-B`**: Raw Vector Score = `0.00` *(absent from vector top results)*, Raw BM25 Score = `15.0`
- **`chunk-C`**: Raw Vector Score = `0.20`, Raw BM25 Score = `3.0`

##### 2. Max Score Identification & Normalization
- Maximum raw vector score: `vector_scores_max = 0.80`
- Maximum raw BM25 score: `keyword_scores_max = 15.0`

Normalized scores (`raw / max`):
- **`chunk-A`**:
  - `vector_score_norm = 0.80 / 0.80 = 1.00`
  - `keyword_score_norm = 12.0 / 15.0 = 0.80`
- **`chunk-B`**:
  - `vector_score_norm = 0.00 / 0.80 = 0.00`
  - `keyword_score_norm = 15.0 / 15.0 = 1.00`
- **`chunk-C`**:
  - `vector_score_norm = 0.20 / 0.80 = 0.25`
  - `keyword_score_norm = 3.0 / 15.0 = 0.20`

##### 3. Score Blending
- **`chunk-A`**: `blended_score = (0.7 * 1.00) + (0.3 * 0.80) = 0.70 + 0.24 = 0.940`
- **`chunk-B`**: `blended_score = (0.7 * 0.00) + (0.3 * 1.00) = 0.00 + 0.30 = 0.300`
- **`chunk-C`**: `blended_score = (0.7 * 0.25) + (0.3 * 0.20) = 0.175 + 0.060 = 0.235`

##### 4. Filtering & Ranking Summary Table

| Chunk ID | Vector Norm | Keyword Norm | Blended Score | Threshold Check (`>= 0.3`) | Final Rank |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `chunk-A` | `1.00` | `0.80` | **`0.940`** | Passed | **Rank 1** |
| `chunk-B` | `0.00` | `1.00` | **`0.300`** | Passed | **Rank 2** |
| `chunk-C` | `0.25` | `0.20` | **`0.235`** | Filtered Out (`< 0.3`) | Excluded |

**Final Output**: Chunks `chunk-A` and `chunk-B` are returned in order of their blended scores. `chunk-C` is excluded.

### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
