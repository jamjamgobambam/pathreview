# Solution plan

**Issue:** [#149 — Structural chunker silently drops documents that contain no headings](https://github.com/ascherj/pathreview/issues/149)

## Understand

`StructuralChunker.chunk()` is supposed to turn non-empty source text into one or more
`Chunk` objects for the RAG index. Instead, a non-empty plain-text document with no Markdown
heading returns `[]` and is silently excluded from indexing.

The root cause is in `_extract_sections()` in
`ingestion/chunking/structural_chunker.py`. Its `else` branch only appends a non-heading line
when `heading_stack` or `current_section_lines` is already truthy. For a document whose first
line is ordinary text, both are empty; each line is discarded. The final-save branch also
requires `heading_stack`, so no section is returned.

**Expected:** a non-empty no-heading document produces a chunk that preserves its text and
source metadata. **Actual:** the existing `test_document_with_no_headings` test expects at
least one chunk, while the current implementation produces zero.

## Map

- `ingestion/chunking/structural_chunker.py`
  - `StructuralChunker.chunk()` converts the extracted sections into `Chunk` objects.
  - `StructuralChunker._extract_sections()` drops content before a heading; this is the defect
    location and the only production function I expect to change.
- `ingestion/chunking/semantic_chunker.py`
  - I will inspect its token-boundary behavior only to make sure a large no-heading document
    gets the same size protection as a large headed section. I do not expect to edit it.
- `tests/unit/test_structural_chunker.py`
  - `test_document_with_no_headings` already defines the failing behavior. I will make its
    assertions specific enough to verify text and fallback metadata, then add only tests needed
    for the selected fallback.
- `JOURNAL.MD`
  - Records the reproduction commit and this plan for the Week 8 submission.

## Plan

1. Run the focused no-heading test before changing code and record its failure. Repair the local
   Python virtual environment first if needed; that setup issue must not be treated as evidence
   about #149.
2. Add a no-heading fallback in `_extract_sections()` for non-empty text. The fallback will
   create a section with the full trimmed document, an empty heading path, and heading level `0`.
   Empty or whitespace-only input will continue to return `[]` from `chunk()`.
3. Make the no-heading test assert the exact fallback contract: one or more non-empty chunks,
   text preserved, source metadata preserved, `heading_path == ""`, and `heading_level == 0`.
   Add a whitespace-only regression check only if the existing test does not already cover it.
4. Run the focused test and all structural-chunker unit tests. Then run `make check` and
   `make test-unit`; fix only regressions caused by this issue.
5. Update this plan if investigation requires touching another file, then commit the fix and
   link the implementation commit in the Week 9 journal entry.

## Inputs & outputs

**Function affected:** `StructuralChunker.chunk(text: str, metadata: dict) -> list[Chunk]`

- Input: `"Plain text with no Markdown headings"` and `{"source": "readme"}`.
  Expected output: at least one `Chunk` containing that text, retaining `source`, with
  `heading_path` set to `""` and `heading_level` set to `0`.
- Input: a headed Markdown document such as `# Title\nBody`.
  Expected output: unchanged headed chunks with the normal heading breadcrumb and level.
- Input: `""` or whitespace only.
  Expected output: `[]`; no empty `Chunk` should be emitted.
- Input: a no-heading document larger than `SECTION_TOKEN_LIMIT`.
  Expected output: non-empty subchunks that preserve the fallback metadata rather than a single
  oversized chunk.

## Risks & unknowns

- A fallback section with an empty heading path may affect consumers that assume every chunk has
  a non-empty breadcrumb. I will search for `heading_path` readers before finalizing the metadata
  contract and update the plan if a consumer needs a different sentinel.
- Large plain text must still obey the 800-token limit. The fallback has to pass through the
  existing semantic chunker rather than bypassing the current size check.
- Documents with text before their first heading currently lose that preamble too. I will decide
  during implementation whether it belongs in a separate level-0 chunk; the selected issue
  guarantees the no-heading case, so I will avoid broadening scope unless a test demonstrates
  the same fallback is necessary.
- The current `.venv` points to a missing Python executable. It blocks normal test commands but
  is not caused by issue #149; I will repair or recreate the environment before relying on the
  full test suite.

## Edge cases

- A document containing only whitespace remains empty and produces no chunks.
- A one-line plain-text document produces a real chunk, not an empty one.
- A long plain-text document is semantically sub-chunked and each resulting chunk keeps source
  metadata plus `heading_path == ""` and `heading_level == 0`.
- A document with valid nested headings keeps its existing `Parent > Child` breadcrumbs.
- A document beginning with a heading but containing an empty section still does not create an
  empty chunk.
