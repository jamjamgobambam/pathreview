## Solution plan

**Issue:** #149 – Structural chunker does not handle headingless documents correctly

### Understand

The `StructuralChunker` class splits Markdown documents into sections based on Markdown headings. During reproduction, I confirmed that a document containing plain text but no headings causes `chunk()` to return an empty list instead of creating a chunk for the document.

Tracing the code showed that `chunk()` calls `_extract_sections()`. Inside `_extract_sections()`, regular text is only collected after a heading has been found. If the document contains no headings, no sections are created and `chunk()` returns an empty list.

The expected behavior is for non-empty headingless documents to still produce at least one chunk instead of losing the document content.

### Map

Files I expect to touch:

- `ingestion/chunking/structural_chunker.py`
  - `chunk()`
  - `_extract_sections()`
- `tests/unit/test_structural_chunker.py`
  - `test_document_with_no_headings()`

### Plan

1. Review `_extract_sections()` to identify why headingless text is ignored.
2. Update the section extraction logic so that non-empty documents without headings still produce a section.
3. Verify that `chunk()` creates a valid `Chunk` object from that section.
4. Run the existing `test_document_with_no_headings` test and confirm it passes.
5. Run the remaining structural chunker unit tests to ensure existing heading behavior is unchanged.
6. Run `make test-unit` and `make check` before opening the pull request.

### Inputs & outputs

**Input**

- Markdown document containing plain text with no headings.

**Current output**

- Returns an empty list (`[]`).

**Expected output**

- Returns one or more `Chunk` objects containing the document text and appropriate metadata.

### Risks & unknowns

- The fallback behavior for headingless documents should preserve the existing behavior for documents that already contain headings.
- I need to verify what metadata should be assigned to chunks that have no heading path.
- I also need to confirm whether very large headingless documents should still be split using the semantic chunker.

### Edge cases

- Empty document.
- Whitespace-only document.
- Document with no headings.
- Document with introductory text before the first heading.
- Very large headingless document.
- Documents containing multiple heading levels.