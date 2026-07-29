# PLAN.md — Issue #149: Structural chunker silently drops documents with no headings

**Issue:** https://github.com/ascherj/pathreview/issues/149
**Tier:** 1 (`tier-1`, `bug`, `good first issue`, `ingestion`)
**Branch:** `fix/149-chunker-drops-documents-w-no-heading`

---

## 1. The problem, restated

`StructuralChunker.chunk()` splits markdown into chunks along heading boundaries
(`#`, `##`, `###`). It only starts collecting text *after* it has seen a heading.
As a result:

- A document with **no headings at all** produces an **empty list** of chunks —
  the whole document is silently dropped.
- A document that has headings but starts with content **before** the first
  heading silently drops that leading content (same root cause).

Because `StructuralChunker` is selected for `source_type == "readme"`
(see `ingestion/chunking/strategy_selector.py:27`), a heading-less or
plain-text README is excluded from the RAG index entirely — no error, no warning —
so it can never be retrieved during search.

---

## 2. Reproduction (done locally, 2026-07-28)

Environment: `.venv` (Python 3.14), no Docker needed — the chunker is pure Python.

**Issue repro snippet:**
```bash
.venv/bin/python -c "
from ingestion.chunking.structural_chunker import StructuralChunker
c = StructuralChunker()
print(len(c.chunk('This is a plain document with no headings at all. ' * 20, {})))
"
# observed: 0
```

**Observed behavior:**
| Input | Chunks produced | Expected |
|-------|-----------------|----------|
| ~1000-char doc, no headings | **0** | ≥ 1 |
| `# Title\nSome content` | 1 | 1 ✓ |
| `Intro line\n# Title\nBody` | 1 (intro line **dropped**) | 2, or intro preserved |

**Failing test (already in the repo):**
```bash
.venv/bin/python -m pytest tests/unit/test_structural_chunker.py -v
# baseline: 14 passed, 1 failed
# FAILED ...::test_document_with_no_headings  (assert 0 >= 1)
```

This is the exact acceptance test — making it pass without breaking the other 14
is the definition of "done."

---

## 3. Root cause

In `ingestion/chunking/structural_chunker.py`, method `_extract_sections()`:

- **Line 111** — `if heading_stack or current_section_lines:` — content lines are
  only collected once a heading has been seen. With no heading, `heading_stack`
  stays empty, so no content is ever appended to `current_section_lines`.
- **Line 115** — `if current_section_lines and heading_stack:` — the final section
  is only saved when `heading_stack` is non-empty. Even if content had been
  collected, a heading-less document would not save it.
- **Lines 89–95** — the mid-loop "save previous section" branch is also gated on
  `heading_stack`, so pre-heading content is dropped when the first heading appears.

Net effect: no headings → `_extract_sections()` returns `[]` → `chunk()` returns `[]`.

---

## 4. Code paths affected (traced)

- `StructuralChunker.chunk()` → `_extract_sections()` (the bug site).
- `chunk()` already sub-chunks any section over `SECTION_TOKEN_LIMIT` (800 tokens)
  via `self.semantic_chunker.chunk(...)` — so if the fix produces a "root" section,
  large heading-less docs get sub-chunked **for free** by existing logic.
- Callers: `StrategySelector.chunk()` → `StructuralChunker` for `source_type=="readme"`
  (`strategy_selector.py:27`), invoked from `ingestion/pipeline.py:101, 176, 249`.
- No other module constructs `StructuralChunker` directly, so blast radius is contained
  to the chunking layer.

---

## 5. Proposed fix

**Approach (chosen): collect pre-heading / no-heading content into a "root" section.**

In `_extract_sections()`, always collect content lines, and when a section is closed
(mid-loop and at end-of-document) with an **empty** `heading_stack`, still emit a
section with an empty heading path (`path=[]`, `level=0`). `chunk()` then treats it
like any other section: small root section → one chunk; large root section →
sub-chunked by the existing semantic-chunker path.

This fixes **both** failure modes (no headings *and* pre-heading content) at the root
cause, rather than papering over only the empty-list symptom.

**Alternative considered — fallback in `chunk()`:** if `_extract_sections()` returns
`[]`, fall back to `self.semantic_chunker.chunk(text, metadata)` on the whole document.
Simpler and satisfies the failing test, but it does **not** fix pre-heading content
loss in documents that *do* have headings, and it splits the fix across two behaviors.
I'm going with the root-section approach; the fallback is the backup if the root-section
change turns out to disturb heading metadata in unexpected ways.

---

## 6. Files to change

| File | Change |
|------|--------|
| `ingestion/chunking/structural_chunker.py` | Fix `_extract_sections()` to collect and emit a root section for heading-less / pre-heading content. |
| `tests/unit/test_structural_chunker.py` | `test_document_with_no_headings` already covers the main case; add a regression test for the **pre-heading content** case and (optionally) a large-no-heading-doc sub-chunking case. |

No changes expected in `strategy_selector.py`, `pipeline.py`, or `base.py`.

---

## 7. Sub-tasks (in order)

1. Confirm baseline (done): 14 pass, `test_document_with_no_headings` fails.
2. In `_extract_sections()`, remove the "only collect after a heading" gate so
   content lines are always buffered.
3. When closing a section with an empty `heading_stack`, emit it with `path=[]`,
   `level=0` — both in the mid-loop save (lines 89–95) and the final save (lines 115–120).
4. Verify `chunk()` handles a root section: `heading_path` becomes `""`, metadata
   still populated, large root sections route through `semantic_chunker`.
5. Run the full structural-chunker suite — target 15 passed, 0 failed.
6. Add a regression test for pre-heading content (assert the intro line survives).
7. Run `make check` (ruff + black + mypy) and the wider unit suite to confirm no
   regressions elsewhere.
8. Commit with a message referencing #149; open PR against `ascherj/pathreview`.

---

## 8. Test / verification plan

- `pytest tests/unit/test_structural_chunker.py -v` → all pass (was 14/15).
- New assertions: heading-less doc returns ≥ 1 `Chunk` with non-empty `.text`;
  pre-heading intro text appears in some chunk's `.text`.
- Sanity: a large (> 800-token) heading-less doc returns **multiple** chunks
  (confirms the sub-chunk path fires).
- `make check` clean.

---

## 9. Risks & edge cases

- **`heading_level = 0` for root sections.** `test_chunk_metadata_includes_heading_level`
  asserts any present `heading_level` is in `[1, 2, 3]`. Its fixture doc starts with a
  heading, so no level-0 chunk is created there — safe today. But level 0 is a new value;
  I'll decide explicitly between `0` and omitting the field for root sections, and check
  no other test asserts membership on a doc with leading content.
- **Empty `heading_path` (`""`).** Existing tests only inspect `heading_path` "if present"
  and never require it non-empty, so `""` is acceptable. Confirm downstream metadata
  consumers don't assume a non-empty path.
- **Whitespace-only / empty input** must still return `[]` — the early guard in `chunk()`
  (`if not text or not text.strip()`) already covers this; `test_empty_input_returns_empty_list`
  and `test_whitespace_only_input` must keep passing.
- **Docs that are all headings, no body** should not regress (existing behavior).
- **Ordering:** pre-heading content must be emitted *before* the first heading's section
  so chunk order matches document order.

---

## 10. Out of scope

- Changing the strategy-selection rules in `strategy_selector.py`.
- Reworking `SemanticChunker`.
- Any API / pipeline changes beyond what the chunk output requires.
