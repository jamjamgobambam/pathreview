## Solution plan

**Issue:** [Structural chunker silently drops documents that contain no headings #149
https://github.com/ascherj/pathreview/issues/149]

### Understand

StructuralChunker.chunk() returns an empty list when processing a document without markdown headings. This causes the document to be skipped during ingestion because no chunks are created for embedding or indexing.

The root cause is in ingestion/chunking/structural_chunker.py inside _extract_sections(). The function only collects content after a markdown heading has been detected. For heading-less documents:
- heading_stack remains empty.
- current_section_lines never receives content.
- The final section is never saved because the save condition requires a heading.

Expected behavior: Heading-less documents should still produce chunks and be included in retrieval.

The fix should happen in _extract_sections() by allowing heading-less content to become a valid section. This allows the existing chunk() logic to continue handling token limits and semantic fallback behavior through SemanticChunker.

### Map
Files involved:

- ingestion/chunking/structural_chunker.py
  - _extract_sections() — currently drops content without headings
  - chunk() — contains existing semantic fallback behavior for large sections

- ingestion/chunking/semantic_chunker.py
  - SemanticChunker.chunk() — existing chunking logic that can be reused for heading-less documents

- tests/unit/test_structural_chunker.py
  - test_document_with_no_headings — existing regression test that should be strengthened.
  - New test for text appearing before the first markdown heading

### Plan
1. Update _extract_sections() so documents without markdown headings are returned as valid sections instead of being dropped.
2. Ensure the existing chunk() flow handles these sections through the normal size checks and SemanticChunker fallback.
3. Preserve metadata for heading-less sections, including an empty heading_path and appropriate heading level.
4. Strengthen test_document_with_no_headings to verify:
   - At least one chunk is returned.
   - Original content is preserved.
   - Source metadata is maintained.
   - Heading metadata uses the expected fallback values.
5. Add a test for pre-heading text to verify that content before the first markdown heading is not dropped.
6. Run the relevant unit tests to confirm existing heading-based chunking behavior remains unchanged.

### Inputs & outputs
Input:
- A document string with or without markdown headings.
- Metadata containing source information

Current output:
- Documents without headings return an empty list

Expected output:
- Heading-less documents are passed through semantic chunking and return one or more valid chunks

### Risks & unknowns
- Adding support for heading-less sections changes current behavior because previously this content was silently ignored.
- Need to confirm the expected metadata values for fallback sections (heading_path, heading_level).
- Need to verify that documents with existing markdown headings continue producing the same chunk structure.
- Need to ensure long heading-less documents still use semantic chunking instead of creating oversized chunks.

### Edge cases
- Empty documents
- Documents containing only whitespace
- Short documents without headings
- Long documents without headings
- Documents containing text before the first markdown heading
- Documents with valid markdown heading sections