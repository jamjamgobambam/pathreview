# Solution plan

## Issue:
Vector store returns stale embeddings after a document is re-ingested  
https://github.com/ZainaNadeem/pathreview/issues/27


## Understand

The issue occurs when an existing document is updated and ingested again, but
the vector store continues returning the previous embedding.

Expected behavior:
When a document changes and is re-ingested, the previous embedding should be
removed or updated and replaced with the new embedding.

Actual behavior:
The old embedding remains in the vector store, causing retrieval results to
contain outdated information.

The suspected root cause is missing update/delete handling during document
re-ingestion.


## Map

Files expected to investigate:

- `src/...` ingestion pipeline
- `src/...` vector store implementation
- `src/...` embedding generation logic
- `tests/...` vector store tests

Functions/modules involved:

- document ingestion flow
- embedding creation
- vector database insert/update operations
- retrieval query logic


## Plan

1. Trace the ingestion flow to identify where existing document embeddings
   are stored and whether previous vectors are removed.

2. Add logic to detect existing documents during ingestion and replace stale
   embeddings instead of creating duplicates.

3. Add tests covering:
   - initial document ingestion
   - document update and re-ingestion
   - retrieval returning updated content

4. Verify that unrelated documents and existing vector search behavior remain
   unchanged.


## Inputs & outputs

Inputs:
- Updated document content
- Document identifier/metadata
- Generated embedding vector

Outputs:
- Updated vector store entry containing the latest embedding
- Retrieval results reflecting current document content


## Risks & unknowns

- Need to confirm whether stale embeddings are caused by duplicate inserts,
  missing deletes, or cache behavior.
- Vector store implementation may have different update semantics depending on
  backend.
- Existing metadata identifiers may not uniquely identify updated documents.


## Edge cases

- Same document ingested multiple times without changes.
- Multiple versions of the same document.
- Failed ingestion after deleting old embeddings.
- Documents removed from the source but still present in the vector store.