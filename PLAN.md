## Solution plan

**Issue:** [Structural chunker silently drops documents that contain no headings (#149)](https://github.com/ascherj/pathreview/issues/149)

### Understand

`StructuralChunker.chunk()` is meant to split a markdown document into chunks along `#`/`##`/`###` heading boundaries and feed each section to the RAG index. Its helper, `_extract_sections()`, walks the document line by line and only appends a content line to `current_section_lines` when `heading_stack or current_section_lines` is truthy (`structural_chunker.py:111`). For a document that never contains a single heading, `heading_stack` stays empty for the entire walk and `current_section_lines` never receives its first line either, so `sections` ends up `[]` and `chunk()` returns `[]`.

- **Expected:** a headingless document should still produce at least one chunk (treated as a single untitled section), the same way `SemanticChunker` already handles headingless text.
- **Actual:** the document is silently dropped — no exception, no log line, no chunks. Since `StructuralChunker` is only invoked for `source_type == "readme"` (see Map below), the practical impact is that any README without markdown headings never makes it into a profile's RAG index, and nothing signals that it happened.

### Map

- `ingestion/chunking/structural_chunker.py` — primary file to change. `chunk()` (line 24) and `_extract_sections()` (line 72) are both involved.
- `ingestion/chunking/semantic_chunker.py` — not modified, but `StructuralChunker` already imports and delegates to `SemanticChunker` for oversized sections (`chunk()` line 56), so the fallback path should reuse this existing, already-tested chunker rather than reimplementing sentence splitting.
- `ingestion/chunking/strategy_selector.py` — not modified, but confirms the blast radius: `StructuralChunker` is selected only for `source_type == "readme"` (line 27), so this bug specifically affects README ingestion.
- `tests/unit/test_structural_chunker.py` — `test_document_with_no_headings` (line 28) already exists and currently fails; I'll extend this file with additional cases rather than writing a new test file.

### Plan

> **Update (Week 9):** Implemented differently than originally planned, and broader in one respect — see notes under each step.

1. ~~Keep `_extract_sections()` untouched, fix only in `chunk()`~~ — **changed:** the fix actually belongs in `_extract_sections()` itself. Instead of a `chunk()`-level fallback that delegates the whole text to `SemanticChunker` when `sections` comes back empty, I removed the faulty guard directly in the extraction loop (`if heading_stack or current_section_lines:` → always collect) and changed section-saving to check for actual content instead of a non-empty `heading_stack`. This is a smaller, more targeted diff and it **also fixes the preamble-before-first-heading bug** (see Risks below) for free, since both symptoms come from the exact same guard.
2. `chunk()` still changed, but differently: instead of a special-case fallback branch, I made `heading_path`/`heading_level` metadata conditional on `section["path"]` being non-empty. A headingless section (or a preamble section) now flows through the *existing* per-section loop — including the existing `SECTION_TOKEN_LIMIT` sub-chunking branch — with no separate code path needed.
3. Metadata shape: confirmed via `grep -rn "heading_path"` that no code outside this file reads it unconditionally, so chunks without a heading path are safe (this resolved the risk noted below, unchanged from original plan).
4. Extended `tests/unit/test_structural_chunker.py`: strengthened `test_document_with_no_headings` to assert actual content survives and that no `heading_path` key is added; added `test_large_headingless_document_is_sub_chunked`, `test_preamble_before_first_heading_is_not_dropped`, and `test_heading_with_no_body_produces_no_chunk_for_it`.
5. Ran `pytest tests/unit/test_structural_chunker.py -v` (18/18 pass, was 14/15) and `make test-unit` (379 passed / 52 failed, vs. a 375/53 baseline — exactly the fix plus 3 new tests, zero regressions elsewhere).

### Inputs & outputs

- **Input:** unchanged — `chunk(text: str, metadata: dict) -> list[Chunk]`. No signature change.
- **Output change:** for a `text` that contains no markdown headings (and isn't blank), `chunk()` now returns `list[Chunk]` with at least one entry (chunked via `SemanticChunker`'s sentence-boundary logic) instead of `[]`. Chunks produced this way will have `SemanticChunker`'s metadata shape (`chunk_index`, `char_start`, `char_end`) rather than `heading_path`/`heading_level`, since there's no heading to report.
- **Unchanged:** blank/whitespace-only input still returns `[]` (line 35-36 behavior is intentional and out of scope).

### Risks & unknowns

- **Metadata shape assumption:** verified via `grep -rn "heading_path" --include="*.py" .` that no code outside `structural_chunker.py` reads `heading_path` — `ingestion/chunking/base.py:20` even documents it as "heading_path if applicable," and the existing tests already guard with `if "heading_path" in chunk.metadata`. So fallback chunks without `heading_path` are safe; this risk is resolved, not open.
- **Preamble-before-first-heading — resolved, fixed in the same PR:** confirmed (see JOURNAL.md Week 8) that text before a document's first heading was dropped by the same guard. Since the actual fix changed the guard in `_extract_sections()` directly (rather than adding a `chunk()`-level fallback), this case is fixed as a natural consequence, not a separate change — covered by `test_preamble_before_first_heading_is_not_dropped`.
- **`SECTION_TOKEN_LIMIT` interplay — resolved:** because headingless/preamble sections now flow through the same per-section loop in `chunk()` as normal sections, they automatically hit the existing sub-chunking branch when oversized — no separate fallback path to keep in sync. Verified with `test_large_headingless_document_is_sub_chunked`.
- **Pre-commit's mypy hook** reports missing type annotations in `structural_chunker.py` and `semantic_chunker.py` (untouched) — confirmed identical on `origin/main` before this change and part of a project-wide pattern (every test file in `tests/unit/` has the same gap). Documented in the PR rather than fixed, to avoid unrelated scope creep across files this issue doesn't touch.

### Edge cases

- A headingless document that exceeds `SECTION_TOKEN_LIMIT` (800 tokens) — must be sub-chunked into multiple pieces via `SemanticChunker`, not returned as one oversized chunk.
- A document with no headings but with `metadata` already containing keys like `source` — those must still be preserved on every fallback chunk (mirrors `test_preserve_source_metadata`, which currently only exercises the heading path).
- A document where the *only* content is a heading with no body text under it (e.g. `"# Title\n"`) — confirm this still returns a chunk (or intentionally an empty list) rather than crashing, since it's adjacent to the no-headings case but not identical.
- Blank/whitespace-only input — must continue returning `[]` unchanged (existing `test_empty_input_returns_empty_list` / `test_whitespace_only_input`), i.e. the fix must not accidentally route blank text into the fallback branch.
