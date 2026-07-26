# Solution plan

**Issue:** [Structural chunker silently drops documents that contain no headings](https://github.com/ascherj/pathreview/issues/149)

**Branch:** `fix/149-handle-documents-without-headings`

## Understand

`StructuralChunker.chunk()` returns an empty list when given a valid, nonempty
document that contains no Markdown headings.

The expected behavior is that the document produces at least one `Chunk`. Short
documents should become one chunk. Large documents should continue to use the
existing semantic sub-chunking behavior (sections over 800 tokens delegate to
`SemanticChunker`).

The actual behavior is that `_extract_sections()` discards every content line
because non-heading lines are only collected when `heading_stack` or
`current_section_lines` is already nonempty. For a document without headings,
both values remain empty, no section is created, `chunk()` returns an empty
list, and the ingestion pipeline continues without storing any chunks or
embeddings (silent data loss, no exception).

The issue was reproduced at runtime using:

* the existing `test_document_with_no_headings` unit test — **FAILED**
  (`assert 0 >= 1`);
* `reproduction/reproduce_issue_149.py` — `Chunks returned: 0`, deterministic
  across two runs;
* a direct diagnostic call to `_extract_sections()` returning `[]`.

See `reproduction/README.md` for full evidence.

## Map

### `ingestion/chunking/structural_chunker.py`

Functions:

```text
StructuralChunker.chunk()
StructuralChunker._extract_sections()
```

Expected change:

* Make `_extract_sections()` return one default untitled section when the input
  is nonempty but no heading-based sections were found.

### `tests/unit/test_structural_chunker.py`

Tests involved:

```text
test_document_with_no_headings
test_empty_input_returns_empty_list
test_whitespace_only_input
test_large_section_sub_chunked
test_preserve_source_metadata
```

Expected change:

* Strengthen the existing heading-less regression test.
* Add a large heading-less document test.
* Confirm metadata defaults and caller-metadata preservation.

### `ingestion/chunking/semantic_chunker.py`

Expected production change: **none currently expected.** `StructuralChunker`
already delegates oversized sections to `SemanticChunker`; this file should be
reviewed and tested but likely does not need modification.

### `tests/unit/test_semantic_chunker.py`

Expected production change: **none currently expected.** Run these tests to
confirm the fallback path remains compatible.

### `reproduction/README.md`

Expected Week 9 update: add post-fix verification results confirming the
original reproduction now produces chunks.

### `docs/contributions/149/INVESTIGATION.md`

Expected Week 9 update: record the verified runtime result and the final
implementation decision.

## Plan

1. Strengthen `test_document_with_no_headings` in
   `tests/unit/test_structural_chunker.py` so it verifies:
   * one or more chunks are returned;
   * the original text is preserved;
   * caller metadata survives;
   * `heading_path` is an empty string;
   * `heading_level` is zero.
2. Add a test for a heading-less document larger than 800 tokens to verify the
   existing semantic sub-chunking path is used and produces valid sequential
   chunk metadata (unique `chunk_index`).
3. Update `StructuralChunker._extract_sections()` so that a nonempty document
   producing no heading-based sections is returned as one untitled section:

   ```python
   {
       "content": text.strip(),
       "path": [],
       "level": 0,
   }
   ```

   The existing `chunk()` loop then yields `heading_path = ""`,
   `heading_level = 0`, and either one chunk (short) or semantic sub-chunks
   (large), reusing current metadata construction and the 800-token threshold.
4. Run the focused regression test, all structural chunker tests, the semantic
   chunker tests, related unit tests, linting (`ruff`), formatting (`black`),
   and the direct reproduction script.
5. Update `reproduction/README.md` and `docs/contributions/149/INVESTIGATION.md`
   with post-fix results before preparing the final contribution.

## Inputs & outputs

### Input

The fix accepts the same inputs as the existing public interface:

```python
StructuralChunker.chunk(text: str, metadata: dict)
```

Relevant input cases: a short heading-less document; a large heading-less
document; an empty string; whitespace-only content; Markdown with one or more
headings; caller metadata such as `source`, `source_id`, `source_type`,
`filename`, `profile_id`, or `repo_name`.

### Expected output for a short heading-less document

A list containing one `Chunk`, with metadata:

```text
heading_path = ""
heading_level = 0
chunk_index = 0
char_start = 0
char_end = document length
```

Caller-provided metadata must be preserved.

### Expected output for a large heading-less document

A list containing multiple semantic sub-chunks when the text exceeds the
existing 800-token section threshold. Each chunk must contain nonempty text,
caller metadata, valid sequential chunk indexes, and heading-context defaults
appropriate for a heading-less document.

### Expected output for empty or whitespace-only content

```python
[]
```

This existing behavior must remain unchanged.

## Risks & unknowns

### Risk: existing heading-hierarchy regressions

Changing `_extract_sections()` could affect Markdown documents containing nested
headings.

Mitigation: run all tests in `tests/unit/test_structural_chunker.py`, paying
particular attention to nested headings, breadcrumbs, multiple H1 headings,
heading levels, and source metadata. (Current baseline: 14 pass.)

### Risk: preamble behavior expands unintentionally

The same guard that drops heading-less documents also drops text before the
first heading (confirmed in the Week 8 investigation).

Mitigation: use a narrow fallback that triggers **only when no structural
sections were produced.** Do not change general preamble handling unless
maintainers confirm it is in scope.

### Risk: large heading-less documents become one oversized chunk

A naïve fallback could bypass the existing 800-token section limit.

Mitigation: return the document as a normal default section so the existing size
check in `chunk()` still delegates large content to `SemanticChunker`.

### Risk: metadata inconsistency

A separate fallback implemented directly in `chunk()` could create metadata that
differs from normal structural chunks.

Mitigation: reuse the existing section loop and metadata-building logic.

### Risk: semantic sub-chunk indexes / embedding-id collisions

The large-document path must preserve valid sequential chunk indexes.
`ingestion/embeddings/batch_processor.py` builds embedding ids as
`"{source_id}_chunk_{chunk_index}"`, so duplicate indexes would collide.

Investigation path:

```text
ingestion/chunking/semantic_chunker.py
ingestion/embeddings/batch_processor.py
tests/unit/test_semantic_chunker.py
```

### Unknown: preamble content scope

It is not yet confirmed whether introductory content before the first heading
should be included in issue #149. This question is not blocking for the narrow
no-heading fix.

## Edge cases

### Empty string

Input: `""` → Expected: `[]`

### Whitespace-only document

Input: `"   \n\n   "` → Expected: `[]`

### One-line heading-less document

Input: `"A short README with no heading."` → Expected: one nonempty `Chunk`.

### Multiline heading-less document

Expected: all nonempty content preserved in one or more chunks.

### Large heading-less document

Expected: divided through the existing semantic sub-chunking path.

### Caller metadata

Input metadata may contain `source`, `source_id`, `source_type`, `filename`,
`profile_id`, `repo_name`, `version`. Expected: all caller metadata survives on
every returned `Chunk`.

### Markdown headings

Documents with H1/H2/H3 headings must continue to preserve section boundaries,
heading breadcrumbs, heading levels, and multiple top-level sections.

### Content before the first heading

Expected Week 8 scope: investigate and document, but do not include in the
production fix unless scope is confirmed by maintainers.

### Heading with no body content

The fallback must not create misleading blank chunks or change existing behavior
for empty heading sections.

---

This file is a living plan, not a fixed contract. It will be updated in Week 9
if the implementation reveals new information.
