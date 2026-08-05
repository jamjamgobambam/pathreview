## Solution plan

**Issue:** [#149 — Structural chunker silently drops documents that contain no headings](https://github.com/ascherj/pathreview/issues/149)

---

### Understand

**Root cause:** `StructuralChunker.chunk()` delegates section discovery to `_extract_sections()`. Inside that method, the `else` branch (which handles non-heading lines) only appends a line to `current_section_lines` when `heading_stack` is truthy:

```python
else:
    # Regular content line
    if heading_stack or current_section_lines:  # Only collect if we have a heading
        current_section_lines.append(line)
```

For a document with no headings at all, `heading_stack` is always empty. `current_section_lines` starts empty too, so this guard is `False` for every line — nothing is collected. The same guard exists in the "save final section" block:

```python
if current_section_lines and heading_stack:   # heading_stack is empty → skipped
```

So `_extract_sections()` returns `[]`, and `chunk()` returns `[]` with no warning.

**Expected behavior:** A document with no markdown headings should be returned as one `Chunk` containing the full document text (or multiple `Chunk` objects if the text exceeds `SECTION_TOKEN_LIMIT`).

**Actual behavior:** `chunk()` returns `[]`, silently discarding the document from the vector index.

---

### Map

Files directly involved:

| File | Role |
|---|---|
| `ingestion/chunking/structural_chunker.py` | Contains the bug in `chunk()` and `_extract_sections()` |
| `tests/unit/test_structural_chunker.py` | Contains `test_document_with_no_headings` (currently failing) |

Files that call `StructuralChunker.chunk()` (impact analysis):

| File | Role |
|---|---|
| `ingestion/chunking/strategy_selector.py` | Selects which chunker to use; may route heading-free docs here |
| `ingestion/pipeline.py` | Orchestrates document ingestion end-to-end |

No schema changes, no API changes, no database migrations required.

---

### Plan

**Sub-task 1 — Add a no-headings fallback in `chunk()` (primary fix)**

After `sections = self._extract_sections(text)`, add a guard:

```python
if not sections:
    # Document has no headings — treat the entire text as one section
    sections = [{
        "content": text.strip(),
        "path": [],
        "level": 0,
    }]
```

This makes `chunk()` continue into the existing loop logic with a single synthetic section. Large heading-free documents will automatically be sub-chunked by `SemanticChunker` because the loop already handles `section_tokens > SECTION_TOKEN_LIMIT`.

**Sub-task 2 — Verify the existing failing test now passes**

Run `pytest tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings -v` and confirm it goes green.

**Sub-task 3 — Run the full structural chunker test suite**

Run `pytest tests/unit/test_structural_chunker.py -v` and confirm no regressions across all existing tests.

**Sub-task 4 — Add an explicit edge-case test for large heading-free documents**

Add a test that feeds a heading-free document exceeding 800 tokens and asserts `len(result) > 1`. This proves the sub-chunking path is exercised for the no-headings fallback, not just the happy path.

**Sub-task 5 — Verify `strategy_selector.py` and `pipeline.py` are unaffected**

Read both files to confirm no caller depends on the current broken behavior (i.e., no caller treats an empty return from `chunk()` as a sentinel meaning "not a markdown document"). Update any comments if needed.

---

### Inputs & outputs

**Input to the fix:**
- `text: str` — any non-empty, non-whitespace document that contains zero markdown headings (e.g., a plain-text resume, a prose README, a code file passed as text)
- `metadata: dict` — arbitrary caller-supplied metadata; unchanged by the fix

**Output after the fix:**
- A `list[Chunk]` with at least one element
- If `len(text tokens) <= 800`: a single `Chunk` with `text=text.strip()`, `metadata` containing `heading_path=""`, `heading_level=0`, `chunk_index=0`, `char_start=0`, `char_end=len(text.strip())`
- If `len(text tokens) > 800`: multiple `Chunk` objects produced by `SemanticChunker.chunk()` with `heading_path=""` and `heading_level=0` in their metadata

**What does NOT change:**
- Behavior for documents that do have headings (they continue through `_extract_sections()` normally)
- The `[]` return for truly empty or whitespace-only input (the early guard at the top of `chunk()` stays)

---

### Risks & unknowns

**Risk 1 — `strategy_selector.py` may check for an empty return as a signal**
If `strategy_selector.py` currently interprets `chunk() == []` as "this document isn't markdown, fall back to semantic chunking," adding a fallback changes that contract. Mitigation: read `strategy_selector.py` before committing (Sub-task 5).

**Risk 2 — `heading_path: ""` may break downstream metadata consumers**
Some RAG retrieval or re-ranking code may filter or sort on `heading_path`. An empty string is a valid value but could sort unexpectedly. Mitigation: search for `heading_path` consumers in `rag/` before the fix is merged.

**Risk 3 — Very large heading-free documents double-process tokens**
The fallback creates a synthetic section object, then the existing loop encodes it with tiktoken to check the token count. For very large docs this is acceptable overhead, but it's worth noting.

**Unknown — Whether `SemanticChunker` preserves `heading_path` from the metadata it receives**
Sub-task 1 relies on `SemanticChunker.chunk()` inheriting `section_metadata` (which includes `heading_path`). Need to confirm that `SemanticChunker` does not overwrite or drop that key. A quick read of `semantic_chunker.py` will resolve this before implementation.

---

### Edge cases

| Input | Expected behavior |
|---|---|
| Document with no headings, ≤ 800 tokens | Single `Chunk` with full text, `heading_level=0` |
| Document with no headings, > 800 tokens | Multiple `Chunk`s from `SemanticChunker`, each with `heading_level=0` |
| Document where the only "heading" is inside a code block (e.g., ```` ```\n# not a heading\n``` ````) | `_extract_sections()` currently matches this as a heading (known pre-existing issue, out of scope for this fix) |
| Document that starts with whitespace before the first real line | `text.strip()` in the fallback ensures the chunk text is clean |
| Document with only a heading and no body content | Already handled by existing logic; not affected by this change |
| Empty string or whitespace-only string | Returns `[]` — unchanged; the early guard at the top of `chunk()` catches this before the fallback is reached |
| Metadata dict is empty `{}` | Works fine; `metadata.copy()` on an empty dict is safe |
