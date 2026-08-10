## Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings

**Issue link:** [[Issue 149](https://github.com/ascherj/pathreview/issues/149)]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

- In `_extract_sections`, content lines are only appended to `current_section_lines` when `heading_stack or current_section_lines` is true. If a document has no headings at all, `heading_stack` never gets populated, so this condition is always false and every content line is dropped.
- At the end of the loop, the final-section save is also gated on `if current_section_lines and heading_stack`. Even if content had been collected, a document with zero headings means `heading_stack` is empty, so the final section is never appended.
- **Expected:** a document with no `#` headings should still produce at least one chunk containing its text (confirmed by `test_document_with_no_headings`, which asserts `len(result) >= 1`).
- **Actual:** `_extract_sections` returns `[]` for headerless input, so `chunk()` also returns `[]` meaning content is silently lost with no error or warning.

### Map
Which files, functions, or modules are involved?

- `ingestion/chunking/structural_chunker.py`
  - `StructuralChunker._extract_sections` — root cause; the two guard conditions above
  - `StructuralChunker.chunk` — consumes the empty `sections` list, so it also needs to handle the "no sections found" case
- `tests/unit/test_structural_chunker.py` — existing regression test (`test_document_with_no_headings`)

### Plan
What are the steps to fix this issue?

1. In `_extract_sections`, remove the `heading_stack or` guard so all content lines are collected into `current_section_lines`, regardless of whether a heading has been seen yet.
2. Handle the "no heading" case explicitly: if `heading_stack` is empty when a section is saved (mid-loop or at the end), still append the section, using an empty `path` (or a sensible default label) and `level = 0` instead of skipping it.
3. Update the mid-loop save condition (`if current_section_lines: ... if heading_stack: ...`) and the final save condition (`if current_section_lines and heading_stack`) so both save content even when `heading_stack` is empty.
4. In `chunk()`, decide how `heading_path`/`heading_level` metadata should look for headerless content (e.g., `heading_path = ""`, `heading_level = 0`) so downstream consumers don't break on a missing key.
5. Run the full unit suite (`pytest tests/unit/test_structural_chunker.py -v`) to confirm `test_document_with_no_headings` now passes and no other tests regress.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

- **Input:** raw markdown `text` (str) and `metadata` (dict) passed to `chunk()`, specifically text with zero `#`-style headings.
- **Output:** a non-empty `list[Chunk]`, where each `Chunk` contains the original text content and metadata that gracefully omits or defaults `heading_path`/`heading_level` instead of assuming a heading always exists.

### Risks & unknowns
What could go wrong? What are you still unsure about?

- Changing the guard conditions could affect how partial documents are handled. content that appears before the first heading in an otherwise well-headed document.
- Large headerless documents still need to pass through the `SECTION_TOKEN_LIMIT` sub-chunking path correctly
- Unsure whether other callers of `_extract_sections` or `chunk()` rely on the current (buggy) behavior of dropping headerless content

### Edge cases
What inputs or states should your fix handle gracefully?

- Fully headerless document
- Document with content before the first heading, followed by properly headed sections
- Document with only headings and no body content under them (`test_empty_sections_handled`)
- Whitespace-only or empty string input (already handled by the early `if not text or not text.strip(): return []` check — confirm this stays correct)
- Headerless document large enough to exceed `SECTION_TOKEN_LIMIT`, to confirm sub-chunking still triggers without a heading path