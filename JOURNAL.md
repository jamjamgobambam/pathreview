# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/149

**Issue title:** Structural chunker silently drops documents that contain no headings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
`StructuralChunker.chunk()` is supposed to split a markdown document into chunks along its heading boundaries, but if a document has no headings at all, it silently returns an empty list instead of chunking the document as a single block. This means any ingested document without markdown headings (a plain-text resume, a README with no `#` sections, etc.) is dropped entirely from the RAG index with no error or warning. The bug lives in `_extract_sections()` in `ingestion/chunking/structural_chunker.py`: content lines are only collected into a section when a heading has already been seen (`heading_stack` non-empty) or a section is already in progress — so for a headingless document neither condition is ever true and nothing is ever collected. A successful fix makes `chunk()` fall back to treating the whole document as a single untitled section when no headings are found, so the content still reaches the index instead of vanishing. I confirmed this is a real, currently-failing bug by running the existing test `test_document_with_no_headings` in `tests/unit/test_structural_chunker.py`, which fails with `assert 0 >= 1` against the current code.

**Selection notes:** I initially considered #146 (PII scrubber phone regex), #147 (resume parser whitespace), and #153 (faithfulness checker `None` crash) — all clean, well-scoped Tier 1 bugs — but each already had 25-38 people commenting that they'd claim it. #149 is functionally identical in scope (single file, existing test file, clear before/after) but had only 13 comments at the time I checked, so I picked it for less crowding while still getting the same kind of practice: read the code, understand the failure, reason about the fix, extend the existing test suite.

**Branch name:** fix/149-structural-chunker-no-headings

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/BarkotBeyene/pathreview/commit/ec85aa2

**Reproduction summary:**
Reproduced the exact snippet from the issue: calling `StructuralChunker().chunk(text, {})` on a 20x-repeated plain-text paragraph with no markdown headings returns `[]`. I also ran the full existing suite, `pytest tests/unit/test_structural_chunker.py`, which shows `test_document_with_no_headings` failing with `assert 0 >= 1` while the other 14 tests in the file pass — confirming the bug is isolated to the no-headings path and everything else in the chunker already behaves correctly.

```
$ python3 -c "
from ingestion.chunking.structural_chunker import StructuralChunker
c = StructuralChunker()
result = c.chunk('This is a plain document with no headings at all. ' * 20, {})
print('chunks returned:', len(result))
"
chunks returned: 0

$ pytest tests/unit/test_structural_chunker.py -v
...
FAILED tests/unit/test_structural_chunker.py::TestStructuralChunker::test_document_with_no_headings
1 failed, 14 passed in 0.91s
```

**PLAN.md link:** [PLAN.md](PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
While tracing the caller (`ingestion/chunking/strategy_selector.py`), I also found that preamble text appearing *before* the first heading in a document that otherwise does have headings gets silently dropped too — same root cause line, different trigger condition. It's not what issue #149 describes, so I'm treating it as an open question for Week 9: fix it in the same PR since it's the same line and same root cause, or leave it out to keep the PR scoped to what the issue actually reports.
