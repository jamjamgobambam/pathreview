# Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings — [ascherj/pathreview#149](https://github.com/ascherj/pathreview/issues/149)

## Understand

**Root cause:** `StructuralChunker._extract_sections()` (in `ingestion/chunking/structural_chunker.py`) only collects content lines *after* a heading has been pushed onto `heading_stack`, and only saves the final section when `heading_stack` is non-empty. For a document with zero markdown headings, no section is ever created, so `chunk()` returns `[]`.

**Expected behavior:** Every non-empty document produces at least one chunk. A document without headings should be chunked as a single block (or fall back to the semantic chunker if it's large), so it still lands in the RAG index.

**Actual behavior:** `chunk()` returns an empty list, and since `StrategySelector` routes all `source_type="readme"` documents to `StructuralChunker`, a heading-less README is silently excluded from the index — no error, no log, no chunks.

**Related defect found during reproduction:** even documents that *do* have headings lose any preamble text that appears before the first heading, for the same reason (content lines before the first heading are never collected).

## Map

Files I expect to touch:

- `ingestion/chunking/structural_chunker.py` — the fix lives here, in `chunk()` and/or `_extract_sections()`.
- `tests/unit/test_issue_149_reproduction.py` — reproduction tests (already committed, currently failing); these become the regression tests and should pass after the fix.
- `tests/unit/test_structural_chunker.py` — `test_document_with_no_headings` already asserts the correct behavior and currently fails; it should pass unchanged after the fix. May add a case for preamble-before-first-heading.

Involved but likely unchanged:

- `ingestion/chunking/strategy_selector.py` — routes `readme` → `StructuralChunker`; no change needed if the chunker itself handles the fallback.
- `ingestion/chunking/semantic_chunker.py` — reused as the fallback for large heading-less documents (already a dependency of `StructuralChunker`).

## Plan

1. **Preserve preamble content in `_extract_sections()`** — collect content lines even when `heading_stack` is empty, and emit a section with an empty heading path (e.g. `path=[]`, `level=0`) for text that precedes the first heading.
2. **Handle the zero-headings case in `chunk()`** — after `_extract_sections()`, the preamble section from step 1 already covers heading-less documents (the whole doc becomes one level-0 section). Verify the existing size check applies: if the section exceeds `SECTION_TOKEN_LIMIT` (800 tokens), it is sub-chunked via `SemanticChunker`, otherwise it becomes a single chunk with `heading_path=""` and `heading_level=0`.
3. **Update the reproduction tests** — remove the "FAILS on current code" framing in `tests/unit/test_issue_149_reproduction.py` so they read as permanent regression tests; confirm all three pass, plus `test_document_with_no_headings` in the existing suite.
4. **Run the full unit suite** (`.venv/Scripts/python -m pytest tests/unit -v -m unit`) to confirm no existing heading-based behavior changed — especially `heading_path` breadcrumbs and sub-chunking of large sections.
5. **Remove the `BUG(#149)` marker comments** from `structural_chunker.py` once the fix is in, and update JOURNAL.md.

## Inputs & outputs

- **Input:** any markdown/plain-text string plus a metadata dict (unchanged signature: `chunk(text: str, metadata: dict) -> list[Chunk]`).
- **Output:** for a non-empty document with no headings — at least one `Chunk` whose metadata carries `heading_path=""` (or a sentinel like the doc title) and `heading_level=0`, with source metadata preserved. Documents with headings keep their current chunking behavior, plus a new chunk for any preamble before the first heading.
- **Downstream change:** heading-less READMEs now appear in the RAG index; retrieval consumers must tolerate an empty `heading_path` string.

## Risks & unknowns

- **Empty `heading_path` downstream:** retrieval/display code may assume `heading_path` is non-empty (e.g. building breadcrumbs in citations). Need to grep `rag/` and `api/` for `heading_path` consumers before finalizing the sentinel value.
- **Chunk count changes for existing docs:** preserving preamble text adds a chunk to documents that have text before their first heading, which could shift `chunk_index` values and any stored embeddings; re-ingestion may be needed for previously indexed docs.
- **Alternative design not chosen:** falling back at the `StrategySelector` level (detect "no headings" and route to `SemanticChunker`) would also work, but fixing it inside `StructuralChunker` keeps the selector simple and also fixes the preamble-loss defect. Will confirm this direction with mentors.
- **`chunk_index` bookkeeping:** the current code sets `chunk_index: len(chunks)` only on non-sub-chunked sections; need to make sure the new level-0 section doesn't produce inconsistent indices when mixed with semantic sub-chunks.

## Edge cases

- Empty string / whitespace-only input → still returns `[]` (current behavior, correct).
- Document with no headings, under 800 tokens → exactly one chunk containing the whole document.
- Document with no headings, over 800 tokens → multiple semantic sub-chunks, none dropped.
- Preamble text before the first heading → preserved as its own level-0 chunk; sections after the heading unchanged.
- Document that is only headings with no body text → should not crash; acceptable to return heading-only chunks or empty list, but must be deliberate.
- Headings using alternate syntax the regex doesn't match (setext `===`/`---` underlines, `#hashtag` without a space) → treated as plain content; with this fix they are safely chunked as text instead of being dropped.
