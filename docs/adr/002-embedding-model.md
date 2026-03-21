# ADR-002: Embedding Model Selection

## Status
Accepted

## Context
We need an embedding model for converting document chunks into vectors for retrieval. Options considered: OpenAI text-embedding-3-small, local sentence-transformers (all-MiniLM-L6-v2), Cohere embed-v3.

## Decision
Use OpenAI text-embedding-3-small as the default, with a provider abstraction that allows swapping models. For local development and testing, use a mock provider that returns deterministic vectors.

## Consequences
- Requires an API key for production use
- Mock provider enables cost-free development and CI
- Provider abstraction adds a small layer of indirection but enables flexibility
