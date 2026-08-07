# Investigation — Issue #149: Structural chunker drops heading-less documents

> Week 7 investigation. All conclusions below are drawn from **static reading**
> of the source. Runtime reproduction is deferred to Week 8.

## 1. Likely execution path

For a README with content but **no `#`-style headings**:

```
IngestionPipeline.ingest_readme(...)          ingestion/pipeline.py:126
  └─ ReadmeParser.parse(content)              ingestion/parsers/readme_parser.py:9
       → ParseResult(text=content, metadata={heading_count: 0, ...})
  └─ StrategySelector.chunk(text, metadata)   ingestion/chunking/strategy_selector.py:34
       → select_chunker("readme") → StructuralChunker
  └─ StructuralChunker.chunk(text, metadata)  ingestion/chunking/structural_chunker.py:24
       └─ _extract_sections(text)             ingestion/chunking/structural_chunker.py:72
            → returns []   ← content is never collected (see §4)
       → chunk() returns []
  └─ BatchEmbeddingProcessor.process([])      ingestion/embeddings/batch_processor.py:26
       → logs warning "Empty chunks list...", returns []  (no exception)
  └─ _record_ingested_source(..., chunk_count=0)
  └─ returns IngestResult(chunk_count=0, skipped=False)   ← "success" with 0 chunks
```

Net effect: the pipeline reports success, records the source as ingested, and
stores **zero embeddings** — the document is silently unretrievable.

## 2. Relevant implementation files

| File | Relevance |
|---|---|
| `ingestion/chunking/structural_chunker.py` | **Primary.** `_extract_sections` is where content is dropped. |
| `ingestion/chunking/base.py` | Defines the `Chunk` dataclass (`text`, `metadata`) and `BaseChunker` interface. |
| `ingestion/chunking/semantic_chunker.py` | Existing plain-text chunker; the structural chunker already delegates to it for oversized sections. Likely reusable for the heading-less fallback. |
| `ingestion/chunking/strategy_selector.py` | Routes `readme` → `StructuralChunker`. |
| `ingestion/pipeline.py` | Consumes chunks; treats `[]` as success (`ingest_readme`, lines 126–199). |
| `ingestion/embeddings/batch_processor.py` | Confirms `[]` is a warning, not an error (line 39). |
| `ingestion/parsers/readme_parser.py` | Produces `heading_count` metadata; `0` is the trigger condition for the bug. |

## 3. Relevant tests

- `tests/unit/test_structural_chunker.py`
  - **`test_document_with_no_headings` (lines 28–35)** — asserts a heading-less
    document returns `len(result) >= 1` (a single chunk). This encodes the
    **expected** post-fix behavior.
  - `test_empty_input_returns_empty_list`, `test_whitespace_only_input` — a fix
    must keep returning `[]` for genuinely empty/whitespace input.
  - `test_large_section_sub_chunked` — confirms the >800-token sub-chunking path.
  - `test_preserve_source_metadata` — caller metadata must survive chunking.
- `tests/unit/test_semantic_chunker.py` — reference for the fallback chunker's
  behavior/metadata if the fix delegates to it.

> Observation (code-supported, not yet runtime-verified): the existing test
> `test_document_with_no_headings` asserts `>= 1` chunk, whereas the current
> `_extract_sections` logic (§4) yields no sections for a heading-less input.
> These appear to be in direct tension. Whether the test currently **fails**
> (vs. is skipped/xfail/otherwise) will be confirmed by reproduction in Week 8;
> it is not asserted here.

## 4. Root cause (directly supported by the code)

In `_extract_sections` (`structural_chunker.py:72`), non-heading lines are only
collected when a guard is already satisfied:

```python
else:
    # Regular content line
    if heading_stack or current_section_lines:  # line 111
        current_section_lines.append(line)
```

- `heading_stack` is only populated when a heading line is matched (line 106).
- `current_section_lines` only grows **inside** this same block.

So for a document with no headings, both are empty on the first content line,
the guard is `False`, and the line is skipped — permanently. `current_section_lines`
never becomes non-empty, so nothing is ever appended.

Two save points then both fail their guards:

- Mid-loop save requires `heading_stack` (line 90) — never true here.
- Final save requires `current_section_lines and heading_stack` (line 115) —
  both false.

Result: `sections == []` → `chunk()` returns `[]`.

**This is a directly code-supported root cause**, not a hypothesis: the guard
on line 111 combined with the guard on line 115 makes it impossible for a
heading-less document to produce any section.

### Related sub-observation (same guard)

The same guard also drops **preamble content that appears before the first
heading** in documents that *do* have headings (e.g. an intro paragraph above
the first `#`). This is caused by the identical condition and may be worth
addressing in the same fix. To be confirmed with reproduction in Week 8 — noted
here, not asserted as in-scope.

## 5. Existing chunker patterns (to reuse / stay consistent with)

- **Empty-guard idiom:** both chunkers start with
  `if not text or not text.strip(): return []` — a fix should preserve this so
  truly empty input still yields `[]`.
- **Delegation for oversized sections:** `StructuralChunker` already calls
  `self.semantic_chunker.chunk(section_text, section_metadata)` when a section
  exceeds `SECTION_TOKEN_LIMIT = 800` (lines 49–57). A natural fix is to route
  heading-less documents through the same `SemanticChunker`, keeping one
  fallback path.
- **Metadata via copy-and-update:** every chunk is built as
  `metadata.copy()` then `.update({...})`, never by mutating the caller's dict.
- **Token counting:** `tiktoken.get_encoding("cl100k_base")` in both chunkers.

## 6. Metadata / interface contract a future fix MUST preserve

The `Chunk` dataclass is `text: str` + `metadata: dict`. Downstream consumers
depend on specific metadata keys:

| Key | Set by | Consumed by | Notes |
|---|---|---|---|
| `source_id` | pipeline | `batch_processor._store_embedding` (line 106) | Part of the embedding ID. |
| `chunk_index` | chunkers | `batch_processor._store_embedding` (line 107) | Forms `"{source_id}_chunk_{chunk_index}"`; must be unique/sequential per source or embedding IDs collide. |
| `heading_path` | structural chunker | tests + retrieval context | For heading-less docs there is no path; a fix must choose a sensible value (e.g. `""`) and stay type-consistent (`str`). |
| `heading_level` | structural chunker | `test_chunk_metadata_includes_heading_level` | `int`; pick a defined default (e.g. `0`) for no-heading chunks. |
| `char_start` / `char_end` | chunkers | metadata / offsets | Present on non-sub-chunked sections and semantic chunks. |
| caller keys (`source_type`, `profile_id`, `repo_name`, `filename`, README parser fields…) | pipeline / parser | retrieval + storage | Must be **preserved** (see `test_preserve_source_metadata`). |

Behavioral invariants a fix must not break:

1. Empty/whitespace input still returns `[]`.
2. Existing heading-based tests continue to pass (nesting, breadcrumb,
   multi-H1, sub-chunking, metadata structure).
3. All caller-supplied metadata keys survive onto every emitted chunk.
4. `chunk_index` remains unique per source (so embedding IDs don't collide).

## 7. What is explicitly NOT concluded yet

- Whether `test_document_with_no_headings` currently passes/fails at runtime
  (Week 8 reproduction).
- The exact chosen fix (fallback to semantic chunker vs. synthesize a default
  section vs. other) — that decision and its `PLAN.md` belong to Week 8.
- Whether the preamble-before-first-heading sub-observation is in scope for #149.

## 8. Week 9 resolution (runtime-confirmed)

The open items from §7 are now resolved against running code (fix commit
`d5a6a906ab54f061e5fd83900625472541bb73df`):

- **`test_document_with_no_headings` did fail at runtime** (`assert 0 >= 1`),
  confirming the Week 7 static tension in §3. It now passes after the fix and was
  strengthened to assert content preservation, caller-metadata survival, and the
  `heading_path=""` / `heading_level=0` defaults.
- **Chosen fix:** synthesize a single default section rather than call
  `SemanticChunker` directly from `_extract_sections`. When a nonempty document
  produces no heading-based sections, `_extract_sections` appends
  `{"content": text.strip(), "path": [], "level": 0}`. This keeps the section
  seam intact, so the existing `chunk()` loop still applies the 800-token
  threshold and delegates oversized heading-less documents to `SemanticChunker` —
  reusing the one fallback path noted in §5 without adding a second entry point.
- **Preamble-before-first-heading remains out of scope for #149.** The fix guard
  (`if not sections and text.strip()`) only fires when *no* heading sections were
  produced, so documents that contain headings — including any preamble above the
  first one — are untouched. The metadata invariants in §6 all hold: empty and
  whitespace input still return `[]`, caller metadata survives, and `chunk_index`
  stays sequential (verified by `test_large_document_with_no_headings_sub_chunked`).

All 16 structural and 16 semantic chunker tests pass. Post-fix reproduction
evidence is captured in `reproduction/README.md`.
