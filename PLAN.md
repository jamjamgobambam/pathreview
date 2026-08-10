## Solution plan

**Issue:** [#149 — Structural chunker silently drops documents that contain no headings](https://github.com/ascherj/pathreview/issues/149)

### Understand

**Root cause:** `StructuralChunker._extract_sections()` only collects content lines when `heading_stack` is non-empty (line 111: `if heading_stack or current_section_lines`). For a document with zero markdown headings, `heading_stack` never gets populated, so `current_section_lines` never begins collecting. The final save (line 115) also requires `heading_stack` to be truthy. The net result is `_extract_sections()` returns `[]`, and `chunk()` therefore returns `[]` — silently discarding the entire document.

**Expected behavior:** Documents without headings should still be chunked and included in the RAG index — either as a single chunk (if small enough) or sub-chunked via `SemanticChunker` (if large).

**Actual behavior:** `chunk()` returns an empty list `[]`, the document is never indexed, and no warning or error is emitted.

### Map

| File | Role |
|------|------|
| `ingestion/chunking/structural_chunker.py` | **Primary fix target** — `_extract_sections()` and `chunk()` methods |
| `ingestion/chunking/semantic_chunker.py` | Fallback chunker used for sub-chunking large sections; will be reused for no-heading fallback |
| `ingestion/chunking/base.py` | `Chunk` dataclass — no changes expected |
| `ingestion/chunking/strategy_selector.py` | Selects chunker by source type — no changes expected (the fix belongs inside `StructuralChunker` itself) |
| `tests/unit/test_structural_chunker.py` | Existing failing test `test_document_with_no_headings` — will pass after fix; may add additional edge-case tests |

### Plan

1. **Add a no-headings fallback in `chunk()`**
   After `_extract_sections()` returns, check if `sections` is empty *and* the input text is non-empty. If so, treat the entire document as a single untitled section and either:
   - Return it as one `Chunk` (if within `SECTION_TOKEN_LIMIT`), or
   - Delegate to `self.semantic_chunker.chunk()` for sub-chunking (if it exceeds the limit).
   Set `heading_path` to `""` (empty string) and `heading_level` to `0` to signal "no heading."

2. **Update `_extract_sections()` to collect pre-heading content**
   Modify the guard on line 111 so that content lines *before* the first heading are also collected. When saving the final section (line 115), handle the case where `heading_stack` is empty by using a default path like `["(untitled)"]`. This ensures mixed documents (text before the first heading + headed sections) don't silently drop the leading content.

3. **Verify existing test passes**
   Run `test_document_with_no_headings` and confirm it now passes (returns `>= 1` chunk with valid `Chunk` instances).

4. **Add targeted edge-case tests**
   - Document with leading text *before* the first heading (mixed content).
   - Single-line plain-text document (minimal input).
   - Document with only whitespace between would-be heading patterns (e.g. `## \n`).

5. **Run full test suite**
   Run `pytest tests/unit/test_structural_chunker.py -v` to ensure no regressions in existing heading-based chunking behavior.

### Inputs & outputs

| | Description |
|---|---|
| **Input** | A markdown string with *no* heading lines (e.g. `"This is plain text."`) and a metadata dict |
| **Expected output** | A non-empty `list[Chunk]` where each chunk contains the document text and metadata with `heading_path: ""`, `heading_level: 0`, `chunk_index`, `char_start`, `char_end` |
| **Currently** | Returns `[]` (empty list) |

### Risks & unknowns

| Risk | Mitigation |
|------|------------|
| **Changing `_extract_sections` could alter chunking behavior for documents that DO have headings** | The fallback only triggers when `sections == []` and the text is non-empty, so headed documents are unaffected. Existing tests cover headed-document behavior. |
| **`SemanticChunker` sub-chunking for large headingless docs may produce different metadata shape** | `SemanticChunker.chunk()` already sets `chunk_index`, `char_start`, `char_end`. We just need to inject `heading_path` and `heading_level` into the metadata before delegating, which matches the existing pattern on lines 51-56. |
| **Downstream consumers of `heading_path` might not handle an empty string or `"(untitled)"`** | Need to check how `heading_path` is used in `rag/` retrieval. A quick grep shows it's stored but not used as a filter key, so empty strings are safe. |
| **`_extract_sections` pre-heading content change could create an extra section** | Must ensure the "pre-heading" section is only emitted when it contains non-whitespace content. Guard with `.strip()` check. |

### Edge cases

| Case | Expected behavior |
|------|-------------------|
| Empty string `""` | Return `[]` (already handled by early return on line 35-36) |
| Whitespace-only `"   \n\n  "` | Return `[]` (already handled by early return) |
| Plain text with no headings | Return `>= 1` chunk(s) — **this is the bug fix** |
| Very large plain text (> 800 tokens, no headings) | Delegate to `SemanticChunker` for sub-chunking |
| Text before the first heading (mixed doc) | Leading text should be captured as its own section with `heading_path: ""` |
| Heading with no content after it (`## Heading\n\n## Next`) | Should produce empty or no chunk for the empty section (existing behavior, already tested) |
| Single-line document (`"Hello world"`) | Return exactly 1 chunk |
