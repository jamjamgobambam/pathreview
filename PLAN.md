## Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings — https://github.com/ascherj/pathreview/issues/149

### Understand
`StructuralChunker.chunk()` is supposed to return at least one chunk for
any non-empty document. Instead, for documents with zero markdown headings,
it returns an empty list. The root cause is in `_extract_sections()`: the
guard `if heading_stack or current_section_lines:` prevents any content
line from being collected until a heading has been seen, because
`heading_stack` only gets populated when a heading regex match occurs.
For headingless documents, `heading_stack` stays empty for the entire
loop, so `current_section_lines` never receives its first line, no
section is ever appended to `sections`, and `chunk()`'s `for section in
sections:` loop simply never runs, silently producing `[]` instead of
raising an error or falling back.

Expected behavior: a document with no headings should be treated as a
single section/chunk (or passed to a fallback strategy), matching the
existing `test_document_with_no_headings` test's expectation of
`len(result) >= 1`.

### Map
- `ingestion/chunking/structural_chunker.py` — `_extract_sections()` (the
  buggy guard) and `chunk()` (where the fallback needs to be added or
  where empty-sections output needs handling)
- `tests/unit/test_structural_chunker.py` — `test_document_with_no_headings`
  is the existing target test; may also add a new test for a headingless
  document that's also over the token limit
- `ingestion/chunking/semantic_chunker.py` — already used as a fallback
  chunker for oversized sections; may be reusable for the no-heading case too

### Plan
1. Modify `_extract_sections()` so that when no heading has been
   encountered, content lines are still collected into an initial
   "no heading" section instead of being silently dropped.
2. In `chunk()`, handle sections with an empty `path` (no heading) by
   using an empty string or `None` for `heading_path` rather than assuming
   at least one heading always exists.
3. Decide whether a headingless document should go straight to
   `SemanticChunker` (consistent with how oversized sections are already
   handled) or be returned as a single `Chunk`, confirmed by checking
   token count against `SECTION_TOKEN_LIMIT` the same way existing
   sections are checked.
4. Run `test_document_with_no_headings` and the full
   `test_structural_chunker.py` suite to confirm the fix doesn't break
   other existing tests, especially `test_empty_sections_handled` and
   `test_whitespace_only_input`, which touch adjacent edge cases.
5. Add a new unit test covering a headingless document that's also over
   `SECTION_TOKEN_LIMIT` tokens, to confirm the sub-chunking fallback
   path works correctly for this case too.

### Inputs & outputs
- **Input:** a `text: str` (markdown, possibly with zero headings) and
  `metadata: dict` (arbitrary document metadata to preserve)
- **Output (current, buggy):** `[]` for headingless text
- **Output (fixed):** `list[Chunk]` with at least one `Chunk`, whose
  `metadata` still includes the original `metadata` keys plus a
  `heading_path` that's empty/`None` (since there's no heading), and
  `heading_level` likely `0` to signal "no heading" rather than a
  fabricated value like `1`.

### Risks & unknowns
- Unsure whether `heading_level: 0` or `heading_level: None` is the
  right convention for headingless sections; need to grep for
  `heading_level` usage in `agent/` and `rag/` to see if anything assumes
  it's always 1-6 before finalizing.
- Fixing `_extract_sections()`'s guard could change behavior for other
  edge cases already covered by `test_empty_sections_handled` (headings
  with no content), so the full test file needs re-running, not just
  the one target test.
- `SemanticChunker.chunk()` (in `semantic_chunker.py`) hasn't been
  inspected yet; if headingless-but-oversized documents get routed
  through it, need to confirm its metadata output shape matches what
  `StructuralChunker` normally attaches.
- Discovered while reproducing this issue that `ruff` and `mypy` both
  flag pre-existing issues in `structural_chunker.py` and
  `semantic_chunker.py` (an unused `current_level` variable, missing
  type annotations) unrelated to this bug; need to decide whether to
  leave these alone or clean them up as part of this PR, since touching
  `semantic_chunker.py` for the fix itself may make its mypy errors
  block `make check`.

### Edge cases
- A headingless document that's short (under `SECTION_TOKEN_LIMIT`),
  should return exactly one `Chunk` with the full text.
- A headingless document that's long (over `SECTION_TOKEN_LIMIT`, e.g.
  the 50x-repeated-paragraph style used in `test_large_section_sub_chunked`),
  should be sub-chunked via `SemanticChunker`, not silently dropped either.
- A document where the first line looks like a heading but is
  immediately followed by headingless content, then more headingless
  content after another non-heading line, confirms the fix doesn't only
  patch the "zero headings ever" case but also doesn't regress normal
  heading-based extraction.
- Whitespace-only input (already handled by the early return in `chunk()`,
  but worth re-confirming `test_whitespace_only_input` still passes after
  the `_extract_sections()` change).
