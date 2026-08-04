---
name: Documentation
about: Improve or add documentation
labels: docs
---

## What Needs Documenting?
Document the structural chunking fallback behavior: documents with valid Markdown headings use heading-aware chunking, while non-empty documents without valid headings use semantic chunking.

## Current State
The structural chunker source documentation and architecture guide now describe the headingless-document fallback and its metadata behavior.

## Proposed Documentation
Document the fallback from an empty structural-section result to `SemanticChunker`, including plain text, headingless lists, and `#hashtag` text. Explain that headingless chunks preserve supplied metadata but do not receive heading-specific metadata.

## Audience and Goal
Ingestion-pipeline maintainers and contributors should be able to predict which chunker handles a document and understand which metadata is present on headingless chunks.

## Relevant Files
- `ingestion/chunking/structural_chunker.py`
- `tests/unit/test_structural_chunker.py`
- `docs/ARCHITECTURE.md`

## Acceptance Criteria
- [x] Documentation states the fallback condition and resulting behavior.
- [x] Examples distinguish valid Markdown headings from hashtag text.
- [x] Documentation uses current module names and matches the tested implementation.
