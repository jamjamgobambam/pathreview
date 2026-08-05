# Solution plan

**Issue:** [Structural chunker silently drops documents that contain no headings](https://github.com/ascherj/pathreview/issues/149) (#149)

## Understand

`StructuralChunker` splits markdown on ATX heading boundaries (`#`, `##`, …). Its helper
`_extract_sections` walks the document line by line, accumulating content lines into
`current_section_lines` and tracking the heading hierarchy in `heading_stack`. Two guards
in that method assume a heading has already been seen:

- **`structural_chunker.py:111`** — `if heading_stack or current_section_lines:` decides
  whether a non-heading line is collected at all. Both are empty until the first heading
  is matched, so every line before the first heading is silently thrown away.
- **`structural_chunker.py:115`** — `if current_section_lines and heading_stack:` decides
  whether the final trailing section is saved. Content that survived collection is still
  discarded if `heading_stack` is empty.

For a document with no headings anywhere, both conditions are false for every line.
`_extract_sections` returns `[]`, the `for section in sections` loop in `chunk()` never
runs, and `chunk()` returns `[]`.

**Expected:** a heading-less document yields at least one chunk covering its full text,
sub-chunked by `SemanticChunker` if it exceeds `SECTION_TOKEN_LIMIT` (800 tokens).

**Actual:** it yields zero chunks.

The failure is silent — no exception, no log line. The empty list flows up through
`StrategySelector.chunk()` into ingestion, so the document is embedded as nothing and
never enters the RAG index. Downstream the review still returns feedback, so a user
uploading a heading-less README gets output that looks legitimate but was generated
without their file ever being read. That silence is what makes this worth fixing
carefully rather than patching the symptom.

Note the guards are not only about *heading-less* documents. In a document that *does*
have headings, the same line-111 guard drops the preamble paragraph before the first
heading — a common README shape (badges, a tagline, an intro sentence, then `## Install`).
I confirmed this in reproduction. It is the same root cause and one line away from the
reported bug.

## Map

Files I expect to touch:

| File | Change |
| --- | --- |
| `ingestion/chunking/structural_chunker.py` | The fix. `_extract_sections` (and possibly a small addition to `chunk()` for fallback metadata). |
| `tests/unit/test_structural_chunker.py` | Add regression tests alongside the existing `test_document_with_no_headings`. |

Files I expect to read but **not** change:

- `ingestion/chunking/base.py` — the `Chunk` dataclass (`text`, `metadata`) my fallback must produce.
- `ingestion/chunking/semantic_chunker.py` — `SemanticChunker.chunk()`, which I reuse for
  oversized fallback content. Already wired up as `self.semantic_chunker`, so no new dependency.
- `ingestion/chunking/strategy_selector.py` — routes `source_type == "readme"` to this
  chunker. Confirms the blast radius: READMEs are the only path that reaches
  `StructuralChunker` today, so no other caller changes behavior.

## Plan

1. **Collect pre-heading content.** Relax the line-111 guard so content lines are always
   accumulated, whether or not a heading has been seen yet.

2. **Flush a section when a heading arrives with no heading context.** When the first
   heading is reached and `current_section_lines` holds preamble text, emit it as a
   section with an empty `path` and `level: 0` rather than dropping it.

3. **Flush the trailing section unconditionally.** Change the line-115 guard from
   `if current_section_lines and heading_stack:` to depend only on there being non-empty
   content. This is what makes a fully heading-less document produce one section.

4. **Make `chunk()` handle a section with no heading path.** A section with `path == []`
   produces `heading_path == ""`. Decide deliberately whether to write an empty
   `heading_path`/`heading_level: 0` or omit those keys, then apply it consistently. The
   existing oversized-section branch already routes through `SemanticChunker`, so a long
   heading-less document gets sub-chunked for free.

5. **Add regression tests.** Beyond the existing `test_document_with_no_headings`: a
   heading-less document long enough to force sub-chunking, and a document with a preamble
   before its first heading asserting the preamble survives.

## Inputs & outputs

**Input:** `chunk(text: str, metadata: dict)` — arbitrary document text that may contain
zero, some, or only ATX headings, plus caller metadata to be preserved on every chunk.

**Output:** `list[Chunk]`. Changes in behavior:

| Input | Before | After |
| --- | --- | --- |
| Heading-less document (< 800 tokens) | `[]` | 1 chunk, full text |
| Heading-less document (> 800 tokens) | `[]` | multiple chunks via `SemanticChunker` |
| Preamble + headings | preamble dropped | preamble kept as its own chunk |
| Empty / whitespace-only | `[]` | `[]` (unchanged) |
| Normal headed document | unchanged | unchanged |

Every chunk keeps the caller's original metadata keys, matching the existing
`metadata.copy()` behavior.

## Risks & unknowns

- **Scope — decided: fix both.** The issue is titled around heading-less documents, but
  the preamble bug comes from the same two guards. I considered fixing only the reported
  case, and rejected it: a reviewer reading the diff would see line 115 changed and line
  111 left alone, four lines apart, with the identical defect still live. That is a worse
  outcome than a slightly larger PR. I will call the wider scope out explicitly at the top
  of the PR description so a maintainer can ask me to narrow it, and I will keep the two
  changes in separate commits so splitting them is cheap if they do.

- **`heading_path` contract.** `heading_path` is currently always a non-empty string.
  Downstream consumers may format or filter on it, and an empty string could surface in a
  citation UI as a stray `" > "` or a blank breadcrumb. I need to grep for `heading_path`
  readers across `rag/` and `api/` before committing to empty-string vs. omitting the key.
  `test_chunk_metadata_includes_heading_level` asserts `heading_level in [1, 2, 3]`, but
  only for chunks that carry the key — so `level: 0` must either be omitted or that test
  needs a deliberate update, and silently changing an existing assertion is exactly the
  kind of thing a reviewer should push back on.

- **`chunk_index` is already wrong.** In the existing code `chunk_index` is set to
  `len(chunks)` only on the non-sub-chunked branch, so indices collide or skip once
  `SemanticChunker` contributes chunks. My fix will add chunks and make this more visible.
  I think this is a **separate bug** and I plan to leave it alone rather than quietly
  widen the PR — but I should note it, and possibly file it as its own issue.

- **Regression surface.** 14 of the 15 existing tests pass today and must keep passing.
  `test_empty_input_returns_empty_list` and `test_whitespace_only_input` are the ones most
  at risk, since a careless "always flush the final section" change could start emitting an
  empty chunk for whitespace-only input. The `.strip()` in the section-save path should
  prevent that, but it needs an explicit assertion, not an assumption.

- **Unknown: intended behavior for a bare heading.** `# Just A Heading` with no body
  currently yields zero chunks. Arguably the heading text is itself content worth
  indexing. I lean toward leaving this alone as out of scope, but I am not certain the
  maintainer agrees.

## Edge cases

The fix should handle these gracefully:

- **Empty string and whitespace-only input** — must still return `[]`, not a chunk of `""`.
  Guarded by the early return in `chunk()` plus `.strip()` on section content.
- **Heading-less document over 800 tokens** — must sub-chunk via `SemanticChunker`, not
  emit one oversized chunk that breaks the embedding model's context limit.
- **Preamble before the first heading** — must be preserved as its own chunk with no
  heading path, not merged into the first heading's section (which would misattribute it).
- **`#NotAHeading`** (no space after `#`) — the regex `^(#{1,6})\s+(.+)$` correctly does
  not treat this as a heading per CommonMark. After the fix it should fall through and be
  captured as ordinary content, which is the right outcome.
- **Setext headings** (`Title` underlined with `===`) — not matched by the ATX-only regex.
  After the fix these documents at least stop vanishing and get chunked as plain text.
  Full setext *support* is a separate feature and explicitly **out of scope** here.
- **Document that is only headings, no body text** — should not emit empty chunks.
- **Content after the last heading** — must still be flushed (covered by step 3).
- **Metadata passthrough** — caller keys like `source` and `version` must survive onto
  fallback chunks, same as the existing `test_preserve_source_metadata` asserts.
