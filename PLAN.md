## Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings — [#149](https://github.com/ascherj/pathreview/issues/149)

### Understand

**Root cause.** `StructuralChunker._extract_sections()` only ever collects
content and emits a section once a markdown heading has been seen:

- `ingestion/chunking/structural_chunker.py` line ~122 — content lines are
  appended only `if heading_stack or current_section_lines`. With no heading,
  `heading_stack` is empty, so nothing is ever collected.
- lines ~93–101 and ~126 — a section is only appended when `heading_stack` is
  truthy (`if current_section_lines and heading_stack`).

So for a document with **no headings at all**, `heading_stack` stays empty for
the whole loop, no section is ever created, `_extract_sections()` returns `[]`,
and `chunk()` returns `[]`. The document is silently excluded from the RAG index.

The *same* guard also drops any **preamble** — content that appears before the
first heading — even in documents that do have headings.

**Expected vs. actual.**
- Expected: a heading-less document is chunked as a single block (or
  sub-chunked via the semantic chunker if it exceeds the token limit), with a
  sensible/empty `heading_path`.
- Actual: `chunk()` returns `[]` and the document never enters the index.

Confirmed reproduction (Week 8):
```
StructuralChunker().chunk("This is a plain document with no headings at all. " * 20, {})
# -> 0 chunks
pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings
# -> FAILED: assert 0 >= 1
```

### Map

Files/functions involved:

- **`ingestion/chunking/structural_chunker.py`** — primary fix.
  - `StructuralChunker._extract_sections()` — the two heading-gated guards that
    drop heading-less content and preamble.
  - `StructuralChunker.chunk()` — consumes sections; already routes large
    sections to the semantic chunker, so a heading-less section will
    automatically be sub-chunked once it is produced.
- **`ingestion/chunking/semantic_chunker.py`** — the fallback for large
  sections; read-only, reused as-is.
- **`tests/unit/test_structural_chunker.py`** — `test_document_with_no_headings`
  is the existing failing test; add coverage for preamble + large heading-less
  docs.

### Plan

1. **Fix content collection in `_extract_sections()`** so regular content lines
   are always collected (remove the `heading_stack`-only gate), letting
   heading-less text and preamble accumulate in `current_section_lines`.
2. **Fix section emission** so a section is appended whenever
   `current_section_lines` has content, regardless of whether `heading_stack`
   is populated. When there is no heading, emit the section with an empty
   `path` (`heading_path == ""`) and `level == 0`. Do this in both the
   mid-loop "save previous section" branch and the final "save final section"
   branch.
3. **Verify the large-doc path**: a heading-less doc over
   `SECTION_TOKEN_LIMIT` (800 tokens) should flow through the existing
   `chunk()` branch into `SemanticChunker`, producing multiple chunks. No new
   code expected here — confirm with a test.
4. **Add/confirm tests**: keep `test_document_with_no_headings` green, add a
   test for a heading-less doc that exceeds 800 tokens (multiple chunks), and
   add a test that preamble-before-first-heading is preserved.
5. **Clean up pre-existing lint** touched by the fix so `make lint`/pre-commit
   pass (unused `current_level`, missing type annotations on `__init__`,
   `heading_stack`, `current_section_lines`).

### Inputs & outputs

- **Input:** `text: str` (arbitrary markdown, possibly with zero headings) and
  `metadata: dict`.
- **Output:** a non-empty `list[Chunk]` for any non-blank input.
  - Heading-less doc → one `Chunk` (or several if > 800 tokens) with
    `heading_path == ""` and `heading_level == 0`, and all original metadata
    preserved.
  - Documents with headings → unchanged behavior, **plus** any preamble now
    appears as its own leading chunk.
  - Empty/whitespace-only input → still `[]` (unchanged).

### Risks & unknowns

- **Regression risk on existing tests.** Emitting preamble as a new chunk
  changes chunk counts for docs whose content starts before the first heading;
  need to re-run the full `test_structural_chunker.py` suite and check for any
  assertions that assume exact counts. (Most existing tests use `>= n`, so this
  should be safe.)
- **`heading_path == ""` downstream.** Unsure whether any consumer of the RAG
  index assumes a non-empty `heading_path`. Investigation path: grep for
  `heading_path` across `rag/`, `ingestion/`, and `api/` before finalizing the
  empty-string choice (alternative: fall back to `metadata["source"]`).
- **`heading_level == 0`.** `test_chunk_metadata_includes_heading_level` asserts
  level ∈ {1,2,3} — but only for chunks that *have* headings, so level 0 for the
  no-heading case should not trip it. Confirm.
- **Pre-existing mypy/ruff failures** in this file block CI; the fix commit must
  resolve them, which slightly widens the diff.

### Edge cases

- Plain document with no headings (the reported bug) — one or more chunks.
- Heading-less document larger than 800 tokens — sub-chunked into multiple
  chunks via `SemanticChunker`.
- Document with preamble text before the first heading — preamble preserved.
- Empty string / whitespace-only — returns `[]` (must not regress).
- Document that is only a heading with no body content — must not crash
  (`test_empty_sections_handled`).
- Content that looks like a heading but is not valid markdown (e.g. `#nospace`,
  or `#` inside a fenced code block) — treated as regular content; current
  regex `^(#{1,6})\s+(.+)$` already requires a space, so `#nospace` is content.
