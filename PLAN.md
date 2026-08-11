# PLAN.md

# Issue #27: Vector store returns stale embeddings after a document is re-ingested

## Problem

My reproduction test confirmed that re-ingesting a document with the same `source_id` leaves stale embeddings in the vector store. Instead of returning the updated document, retrieval still returns the old version.

## Files

- `ingestion/embeddings/batch_processor.py`
- `rag/vector_store.py`
- `tests/unit/test_batch_processor.py`

## Plan

1. Trace the re-ingestion workflow to determine why old embeddings remain.
2. Update the storage logic so embeddings for the same `source_id` are replaced during re-ingestion.
3. Run the reproduction test and existing unit tests to verify the fix and ensure nothing else breaks.

## Inputs

- Original document
- Updated document
- The same `source_id` for both ingestions


## Expected Output

- Old embeddings are replaced after re-ingestion.
- Retrieval returns the updated document.
- Existing ingestion behavior continues to work correctly.

## Risks

- The root cause may be in `BatchEmbeddingProcessor`, `VectorStore`, or another part of the ingestion pipeline.
- Changes to the storage logic could affect existing ingestion behavior.

## Edge Cases

- Re-ingesting a document with multiple chunks.
- Re-ingesting the same document multiple times.
- Re-ingesting one document while other documents exist in the same vector store.