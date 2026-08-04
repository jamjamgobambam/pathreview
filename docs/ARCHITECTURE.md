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

#### Hybrid Retrieval Scoring Logic
The retrieval system utilizes a hybrid scoring method for chunks by summing both normalized (0-1) vector and keyword scores multiplied by their respective weights, with vector being 0.7 and keyword being 0.3. Scores will range from 0 - 1, with 0 corresponding to a chunk having no relevance and 1 having the most relevance. 

##### Normalization
Each chunk's keyword and vector is normalized as the proportion of the raw score to the max raw score of each result set. 

Ex: If a keyword raw score is 3, and the max keyword score is 5, then the normalized raw score for that individual keyword is 3/5 = 0.6

##### What if a chunk is missing from result sets?
The chunk does not need to appear in both vector and keyword sets. If it is missing from either one, that side will have a score of 0, and the score will reflect that absence. 

Example:
| Chunk | Vector Score | Keyword Score | Normalized Vector | Normalized Keyword | Blended (0.7v + 0.3k) |
|---------|---------|---------|---------|---------|---------|
A | 0.3 | 0.0 | 0.500| 0.000 | 0.350 
B | 0.0 | 4.0 | 0.000 | 1.000 | 0.300| 
C | 0.6 | 1.0 | 1.000 | 0.250 | 0.775| 
A | 0.2 | 2.0 | 0.333 | 0.500 | 0.381| 




### Safety Layer (`safety/`)
Middleware wrapping the generation pipeline. Components run in sequence: prompt injection defense → content filter → bias detector → PII scrubber. All safety events are logged with structured metadata for monitoring.

## Key Design Decisions

See the Architecture Decision Records in `docs/adr/` for context on major decisions:
- [ADR-001: Chunking Strategy](adr/001-chunking-strategy.md)
- [ADR-002: Embedding Model Selection](adr/002-embedding-model.md)
- [ADR-003: Agent Orchestration Approach](adr/003-agent-orchestration.md)
