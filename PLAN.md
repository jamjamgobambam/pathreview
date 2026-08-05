## Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings — #149
https://github.com/ascherj/pathreview/issues/149

### Understand
`StructuralChunker.chunk()` delegates to `_extract_sections()` to split text on
markdown headings. When no headings exist, two guards in `_extract_sections` prevent
content from ever being collected or saved:

1. The line-collection guard — `if heading_stack or current_section_lines` — starts
   false for every line in a heading-free document because `heading_stack` is empty
   and `current_section_lines` is empty, so no content is ever appended.
2. The final save — `if current_section_lines and heading_stack` — is also gated on
   `heading_stack`, so even if content were collected, it would not be returned.

Result: `_extract_sections` returns `[]`, `chunk()` loops over nothing, and the
document is silently dropped from the RAG index. Expected behavior: a heading-free
document should be returned as a single `Chunk` containing the full text, with an
empty `heading_path` and `heading_level` of 0.

### Map
Files I will touch:
- `ingestion/chunking/structural_chunker.py` — fix `_extract_sections` to collect
  and return heading-free content as a single section
- `tests/unit/test_structural_chunker.py` — the failing test
  `test_document_with_no_headings` already exists and defines the expected behavior;
  the fix should make it pass without modifying the test

### Plan
1. In `_extract_sections`, remove the `heading_stack` requirement from the
   line-collection guard so content lines are always appended:
   change `if heading_stack or current_section_lines` → `if True` (or just remove
   the condition entirely since all non-heading lines should be collected)
2. In `_extract_sections`, add a fallback at the final save block: if
   `current_section_lines` is non-empty but `heading_stack` is empty, append a
   section with an empty `path` and `level` of 0
3. Verify the fallback section flows correctly through `chunk()` — `heading_path`
   will be `""` (join of empty list) and `heading_level` will be `0`, which is valid
4. Run `test_document_with_no_headings` to confirm it passes
5. Run the full unit suite (`make test-unit`) to confirm no regressions

### Inputs & outputs
Input: plain text string with no markdown headings, e.g.
`"This is a plain document with no headings at all. " * 20`

Output: a list containing one `Chunk` object where:
- `chunk.text` contains the full document text (stripped)
- `chunk.metadata["heading_path"]` is `""`
- `chunk.metadata["heading_level"]` is `0`

### Risks & unknowns
- The line-collection guard change could affect documents that have content
  before the first heading — need to verify those still produce correct output
  and don't create an extra leading chunk (currently that pre-heading content
  is also silently dropped, which may or may not be intentional)
- `heading_path` being an empty string for the fallback chunk is fine for the
  test, but worth checking whether any downstream RAG code filters on or
  expects a non-empty `heading_path`

### Edge cases
- Empty string: already handled by the early return in `chunk()` — returns `[]`
- Whitespace-only string: same early return — returns `[]`
- Document with content before the first heading: currently also dropped;
  the fix may surface this as a separate chunk with empty path — acceptable
  for now but worth noting
- Single sentence with no heading: should produce exactly one chunk
- Heading-free document exceeding 800 tokens: the fallback section will trigger
  the semantic sub-chunker path inside `chunk()`, which is correct behavior