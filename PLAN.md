## Solution plan

**Issue:** [#149 - Structural chunker silently drops documents that contain no headings](https://github.com/ascherj/pathreview/issues/149)

### Understand

**Root cause:** `StructuralChunker._extract_sections()` (`ingestion/chunking/structural_chunker.py`, lines 76-133) only starts collecting body lines once it has seen at least one Markdown heading — the guard on line 120 (`if heading_stack or current_section_lines`) is `False` for every line whenever `heading_stack` never gets populated. For a document with zero `#`/`##`/`###` lines, `heading_stack` stays empty for the entire loop, nothing is ever collected, `sections` ends up `[]`, and `chunk()` (lines 24-74) returns `[]`.

**Expected vs. actual:**
- Expected: a document without headings should still produce at least one chunk so it gets indexed.
- Actual: `chunk()` silently returns `[]` — confirmed and documented in commit [54ff459](https://github.com/ShiriZhang/pathreview/commit/54ff4590b6f6ceb8d561a684f2dfa8f153c20c9e) via `pytest tests/unit/test_structural_chunker.py -k test_document_with_no_headings -v`, which fails with `assert 0 >= 1`.

### Map

- `ingestion/chunking/structural_chunker.py` — `StructuralChunker.chunk()` (lines 24-74) and `_extract_sections()` (lines 76-133): where the fix goes
- `ingestion/chunking/semantic_chunker.py` — `SemanticChunker.chunk()`: candidate fallback for headless documents; already handles empty/whitespace input independently
- `ingestion/chunking/strategy_selector.py` — confirms `StructuralChunker` is only used when `source_type == "readme"`, which bounds the blast radius
- `tests/unit/test_structural_chunker.py` — `test_document_with_no_headings` (lines 28-35) is the existing failing test the fix must satisfy

### Plan

1. In `_extract_sections()`, detect the case where no headings were found at all (`sections` is empty after the loop but `text` was non-empty)
2. Choose a fix strategy: (a) treat the whole document as a single section (`path=[]`, `level=0`) and let the existing large-section logic in `chunk()` route it through `SemanticChunker` if it exceeds `SECTION_TOKEN_LIMIT`; or (b) short-circuit in `chunk()` and delegate the entire text to `self.semantic_chunker.chunk(text, metadata)` when no sections were found
3. Implement the fix without changing existing heading-based behavior
4. Run `pytest tests/unit/test_structural_chunker.py -v` to confirm `test_document_with_no_headings` passes and nothing else regresses
5. Run `make check && make test-unit` before opening the PR

### Inputs & outputs

- **Input:** raw text (`str`) + `metadata: dict` (e.g. `{"source_type": "readme"}`)
- **Output today:** `[]` when there are no headings
- **Output after fix:** a non-empty `list[Chunk]`; metadata will carry either heading info (`heading_path`, `heading_level`) or whatever `SemanticChunker` attaches (`chunk_index`, `char_start`, `char_end`), depending on which strategy is chosen

### Risks & unknowns

- Not yet decided between option (a) or (b) above — plan to check linked PRs #192 and #162 for precedent before finalizing
- If using (a), need to confirm no downstream RAG/retrieval code assumes `heading_path` is always non-empty for `source_type="readme"` documents
- If using (b), resulting chunks won't have `heading_path`/`heading_level` keys at all — need to confirm nothing downstream requires those keys unconditionally
- **Pre-existing lint/type debt (unrelated to #149):** touching `structural_chunker.py` for the reproduction comment surfaced pre-existing `ruff`/`mypy` failures in both `structural_chunker.py` and its import, `semantic_chunker.py` (unused `current_level` variable, unused loop index, 7 missing type annotations). Initially suspected this was caused by the fork being out of sync with `upstream/main`, but verified directly against a clean `upstream/main` checkout that the same issues exist there too — confirmed genuine pre-existing debt, not a sync artifact. Cleaned it up in commit [54ff459](https://github.com/ShiriZhang/pathreview/commit/54ff4590b6f6ceb8d561a684f2dfa8f153c20c9e) since it was blocking any commit that touches these files (mypy checks the full import graph, so it can't be scoped to one file alone).

### Edge cases

- Whitespace-only input — already handled correctly today (returns `[]`, per `test_whitespace_only_input`); must not regress
- Very short headless document (a few words) — should yield exactly 1 chunk
- Long headless document exceeding `SECTION_TOKEN_LIMIT` (800 tokens) — should sub-chunk via `SemanticChunker` rather than produce one oversized chunk
- A line that looks like a heading but doesn't match the regex (e.g. `#nospace`) — must not be mistaken for a real heading; current regex `^(#{1,6})\s+(.+)$` already requires a space after `#`, so this should already be safe — worth a regression test
