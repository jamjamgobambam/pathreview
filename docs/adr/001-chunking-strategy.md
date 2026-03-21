# ADR-001: Chunking Strategy Selection

## Status
Accepted

## Context
PathReview processes two types of documents with different structures: resumes (semi-structured, section-based) and READMEs (markdown with heading hierarchy). A single chunking strategy doesn't serve both well.

## Decision
Use a strategy dispatcher that selects the chunking approach based on document type:
- **Resumes** → Semantic chunker (split on meaning boundaries)
- **READMEs** → Structural chunker (split on markdown headings, preserving hierarchy)

## Consequences
- Two chunkers to maintain instead of one
- Better retrieval quality for both document types
- Pipeline must know the document type before chunking
