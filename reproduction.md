# Issue #27 Reproduction

## Steps

1. Ingest document with initial content:
   "The company was founded in 2020."

2. Query vector store.

3. Update document:
   "The company was founded in 2025."

4. Re-ingest document.

5. Query again.

## Expected

Vector store should return the updated embedding/content.

## Actual

Old embedding remains and stale document information is returned.