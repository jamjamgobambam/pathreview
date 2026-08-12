# Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings — https://github.com/ascherj/pathreview/issues/149

### Understand

**Root cause.** `StructuralChunker._extract_sections()` only records content
*after* a Markdown heading has been seen. Two guards enforce this:

- The content-collection guard (`if heading_stack or current_section_lines:`)
  never fires for a heading-less document, because `heading_stack` stays empty
  and `current_section_lines` therefore never receives its first line.
- The final-section guard (`if current_section_lines and heading_stack:`)
  additionally requires `heading_stack` to be non-empty before emitting the
  trailing section.

So a non-empty document with no `#` headings produces **zero** sections, and
`chunk()` returns `[]`.

**Expected vs. actual.**

| Input | Expected | Actual |
| --- | --- | --- |
| `"plain text ..." * 20` (no headings) | ≥ 1 `Chunk` | `[]` |
| Document with headings | unchanged | unchanged (works today) |

**Impact.** Heading-less documents (plain-text notes, pasted resumes, PDFs
with no Markdown structure) are silently excluded from the RAG index and can
never be retrieved. Failure is silent — no error, just missing data.

Reproduced in Week 8: `chunk("...", {})` returns `[]`, and
`tests/unit/test_structural_chunker.py::test_document_with_no_headings` fails
with `assert 0 >= 1`.

### Map

Files/functions involved:

- `ingestion/chunking/structural_chunker.py`
  - `StructuralChunker.chunk()` — where the empty `sections` list currently
    yields `[]`; best place to add the fallback.
  - `StructuralChunker._extract_sections()` — the two guards that are the root
    cause.
- `ingestion/chunking/semantic_chunker.py` — existing, tested chunker to reuse
  as the fallback (handles token limits + overlap for long plain text).
- `tests/unit/test_structural_chunker.py` — `test_document_with_no_headings`
  is the acceptance test; add a few more cases.

**Files I expect to touch:** `ingestion/chunking/structural_chunker.py` and
`tests/unit/test_structural_chunker.py`.

### Plan

1. In `chunk()`, after `sections = self._extract_sections(text)`, detect the
   "no sections extracted but text is non-empty" case and fall back to the
   semantic chunker: `self.semantic_chunker.chunk(text, metadata)` with a
   `heading_path=""` / `heading_level=0` in metadata. This produces ≥ 1 chunk
   and correctly sub-chunks long documents by token budget.
2. (Optional, related) Also capture content that appears *before* the first
   heading (preamble) so it isn't dropped — likely by relaxing the collection
   guard and emitting a level-0 section. Keep this small and behind the same
   fix; do not regress heading behavior.
3. Add unit tests: short no-heading doc → exactly 1 chunk; long no-heading doc
   (> 800 tokens) → multiple chunks; whitespace-only → still `[]`; source
   metadata preserved on the fallback path.
4. Run the full structural + semantic chunker test suites and `ruff` to
   confirm no regressions.
5. Update `JOURNAL.md` (Week 9) with the fix summary and open the PR.

### Inputs & outputs

- **Input:** `text: str` (arbitrary document, may contain zero headings) and
  `metadata: dict`.
- **Output:** `list[Chunk]`. New guarantee: for any `text` where
  `text.strip()` is non-empty, `len(result) >= 1`. Each fallback `Chunk`
  carries the original metadata plus `chunk_index`, `char_start`, `char_end`
  (from the semantic chunker) and `heading_path=""`.
- **Unchanged:** empty/whitespace input still returns `[]`; documents with
  headings produce the same chunks as today.

### Risks & unknowns

- **Metadata shape.** Downstream indexing may assume `heading_path` /
  `heading_level` keys exist. Need to confirm what the indexer expects for a
  headingless chunk (empty string vs. missing key). Will check the ingestion
  pipeline that consumes `Chunk.metadata`.
- **Double-counting `chunk_index`.** The semantic chunker sets its own
  `chunk_index` starting at 0; make sure mixing fallback and heading paths
  never happens in one call (it can't — fallback only fires when `sections`
  is empty), so indices stay consistent.
- **Preamble change (step 2)** could subtly alter output for docs that have
  both a preamble and headings; must be covered by a test before shipping, or
  deferred to keep scope tight.

### Edge cases

- Whitespace-only / empty input → `[]` (must stay).
- Single short line, no heading → exactly 1 chunk.
- Very long plain text (> `SECTION_TOKEN_LIMIT` 800 tokens) → sub-chunked into
  multiple chunks via the semantic chunker.
- Text that looks like a heading but isn't (`#nohash`, `#### ` with no text) →
  treated as content, still chunked.
- Document with content before the first real heading (preamble) → not dropped.
- Non-ASCII / emoji content → chunked without error (tiktoken handles it).
