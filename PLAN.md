## Solution plan

**Issue:** Structural chunker silently drops documents that contain no headings — https://github.com/ascherj/pathreview/issues/149

### Understand
The `StructuralChunker` splits markdown into sections on heading boundaries
(`#`, `##`, `###`, …). When a document has **no** headings anywhere, it produces
**zero chunks** and returns them silently — the document is never processed or
stored, and no error or warning is surfaced.

Root cause is in the `_extract_sections` function in
`ingestion/chunking/structural_chunker.py`: **a section is only ever created as
a side effect of matching a heading.**

- A content line is only accumulated when `heading_stack or current_section_lines`
  is already truthy (the `else`-branch guard, line 111).
- The final-section save requires `current_section_lines and heading_stack`
  (line 115).
- `heading_stack` only ever becomes non-empty inside the `if heading_match:`
  branch (line 87).

So if `re.match(r"^(#{1,6})\s+(.+)$", line)` never matches (no heading in the
whole doc), `heading_stack` stays empty, every content line is discarded at
line 111, and the final save at line 115 is skipped. `_extract_sections` returns
`[]` → `chunk()` returns `[]`.

Note this is *not* a `split("\n")` problem: `text.split("\n")` on the failing
input (one long line, no newline) still yields a one-element list and the loop
runs — the drop is driven entirely by the missing heading match, not by line
count.

**Expected:** a heading-free document is chunked as a whole unit (one chunk, or
semantically sub-chunked if it exceeds `SECTION_TOKEN_LIMIT`), with sensible
metadata.
**Actual:** `chunk()` returns `[]`, so the document is dropped.

### Map
Files/functions I expect to touch:

- `ingestion/chunking/structural_chunker.py`
  - `StructuralChunker._extract_sections` — add a fallback so text with no
    heading match still yields one section (empty `path`, `level` 0), and so
    pre-heading content is collected rather than discarded.
  - `StructuralChunker.chunk` — ensure a section with an empty `path` produces a
    valid `heading_path` (empty string) and still routes through the
    single-chunk / semantic-sub-chunk logic.
- `ingestion/chunking/base.py` — reference only, to confirm the `Chunk` dataclass
  fields and `metadata` contract.
- `ingestion/chunking/semantic_chunker.py` — reference only, to confirm the
  fallback path for oversized headingless docs.
- `tests/unit/test_structural_chunker.py` — `test_document_with_no_headings` is
  the existing failing test; may add cases for pre-heading preamble and oversized
  headingless docs.

### Plan
1. In `_extract_sections`, relax the line-111 guard so content is collected even
   before any heading is seen (so pre-heading text isn't silently dropped).
2. After the loop, when content remains but **no** heading was ever matched
   (`heading_stack` empty), append a single fallback section:
   `{"content": <stripped text>, "path": [], "level": 0}`.
3. In `chunk()`, confirm `" > ".join([])` → `""` flows through the existing
   token-count branch: small headingless docs become one `Chunk`; docs over
   `SECTION_TOKEN_LIMIT` route to `semantic_chunker` with `heading_path=""`.
4. Run `test_document_with_no_headings` to confirm it passes, then run the full
   `test_structural_chunker.py` suite to confirm no regression in heading cases.

### Inputs & outputs
- **Input (unchanged signature):** `chunk(text: str, metadata: dict) -> list[Chunk]`.
- **Behavior change:** for headingless (or pre-heading) content, `chunk()` now
  returns `>= 1` `Chunk` instead of `[]`.
- **Metadata produced for the fallback chunk:** `heading_path=""`,
  `heading_level=0`, plus the existing `chunk_index`, `char_start`, `char_end`,
  and any caller-supplied keys (e.g. `source`).
- **Unchanged:** truly empty / whitespace-only input still returns `[]`
  (the `if not text or not text.strip()` guard at line 35).

### Risks & unknowns
- **Downstream `heading_path=""` assumptions:** consumers of chunk metadata
  (retrieval / display in `rag/`) may expect a non-empty `heading_path`; an empty
  string could render oddly. Grep usages of `heading_path` before finalizing.
- **`_extract_sections` refactor regressions:** relaxing the line-111 guard risks
  mis-attributing pre-heading preamble to the first heading's section — the
  nested/mixed-heading tests (`test_document_with_nested_headings`) must still pass.
- **Oversized headingless docs:** unclear whether `semantic_chunker.chunk` behaves
  well with an empty `heading_path` in metadata — needs a direct check.
- **`level`/`path` typing:** downstream code may assume `path` is non-empty when
  computing `heading_level`; verify `level=0` / `path=[]` is tolerated.

### Edge cases
1. Document with **no headings at all** (the failing test) → exactly one chunk.
2. Headingless document **longer than `SECTION_TOKEN_LIMIT` (800 tokens)** →
   multiple semantic sub-chunks, none dropped.
3. Document with **leading paragraphs before the first heading**, then headings →
   the preamble is preserved as its own chunk, not silently dropped.
4. **Empty / whitespace-only** input → still returns `[]` (must not regress).
5. Document that is a **single heading line with no body content** → handled
   without producing an empty-content chunk or crashing.
