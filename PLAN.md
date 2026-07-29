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

1. In `_extract_sections()`, keep the existing heading-walk logic untouched (it already passes 14/15 tests) — the fix belongs in `chunk()`, not in the extraction loop itself.
2. In `chunk()`, after calling `_extract_sections(text)`, check if `sections` is empty. If it is (and the input text wasn't blank — that early-return at line 35-36 stays as-is), delegate the whole `text` to `self.semantic_chunker.chunk(text, metadata)` and return its result directly, instead of returning `[]`.
3. Decide what metadata the fallback chunks carry: since there's no heading, they won't have `heading_path`/`heading_level` — confirm no downstream consumer assumes those keys always exist (see Risks).
4. Extend `tests/unit/test_structural_chunker.py`: strengthen `test_document_with_no_headings` to assert the returned chunk(s) actually contain the original text (not just `len(result) >= 1`), and add a case for a headingless document long enough to exceed `SECTION_TOKEN_LIMIT` (800 tokens) to confirm it gets sub-chunked via `SemanticChunker` rather than returned as one giant chunk.
5. Run `pytest tests/unit/test_structural_chunker.py -v` and `make test-unit` to confirm the fix doesn't regress the 14 currently-passing tests or anything else in the suite.

### Inputs & outputs

- **Input:** unchanged — `chunk(text: str, metadata: dict) -> list[Chunk]`. No signature change.
- **Output change:** for a `text` that contains no markdown headings (and isn't blank), `chunk()` now returns `list[Chunk]` with at least one entry (chunked via `SemanticChunker`'s sentence-boundary logic) instead of `[]`. Chunks produced this way will have `SemanticChunker`'s metadata shape (`chunk_index`, `char_start`, `char_end`) rather than `heading_path`/`heading_level`, since there's no heading to report.
- **Unchanged:** blank/whitespace-only input still returns `[]` (line 35-36 behavior is intentional and out of scope).

### Risks & unknowns

- **Metadata shape assumption:** verified via `grep -rn "heading_path" --include="*.py" .` that no code outside `structural_chunker.py` reads `heading_path` — `ingestion/chunking/base.py:20` even documents it as "heading_path if applicable," and the existing tests already guard with `if "heading_path" in chunk.metadata`. So fallback chunks without `heading_path` are safe; this risk is resolved, not open.
- **Preamble-before-first-heading is a related but separate bug:** I confirmed (see JOURNAL.md Week 8) that text appearing *before* the first heading in a document that otherwise has headings is also silently dropped, by the same `heading_stack or current_section_lines` condition. My planned fix (checking `if not sections`) does **not** cover this case, since `sections` would be non-empty. Open question for Week 9: fix both in one PR since they share a root cause, or keep this PR scoped strictly to what #149 reports and file a follow-up.
- **`SECTION_TOKEN_LIMIT` interplay:** need to verify the fallback path correctly hits the existing sub-chunking branch (line 49) for large headingless documents rather than accidentally bypassing it, since I'm calling `semantic_chunker.chunk()` directly rather than going through the `sections` loop.

### Edge cases

- A headingless document that exceeds `SECTION_TOKEN_LIMIT` (800 tokens) — must be sub-chunked into multiple pieces via `SemanticChunker`, not returned as one oversized chunk.
- A document with no headings but with `metadata` already containing keys like `source` — those must still be preserved on every fallback chunk (mirrors `test_preserve_source_metadata`, which currently only exercises the heading path).
- A document where the *only* content is a heading with no body text under it (e.g. `"# Title\n"`) — confirm this still returns a chunk (or intentionally an empty list) rather than crashing, since it's adjacent to the no-headings case but not identical.
- Blank/whitespace-only input — must continue returning `[]` unchanged (existing `test_empty_input_returns_empty_list` / `test_whitespace_only_input`), i.e. the fix must not accidentally route blank text into the fallback branch.
