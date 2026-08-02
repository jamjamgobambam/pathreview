## Week 7 - Issue Selection

**Issue Link:** https://github.com/ascherj/pathreview/issues/149

**Issue Title:**Structural chunker silently drops documents that contain no headings(149)

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The structural chunker is supposed to break a document into pieces so the app can
search through them, and it does this by splitting the text wherever it finds a
heading (like `#` or `##`). The problem is that it only starts saving text *after*
it sees a heading, so if a document has no headings at all, nothing gets saved and
the whole document just disappears without any error or warning. The fix is to make
sure text that comes before or without any heading still gets collected into a
chunk, so that every document actually makes it into the system instead of being
silently thrown away. This all happens in the `_extract_sections` method in
`ingestion/chunking/structural_chunker.py`.

**Branch name:** fix/149-chunker-drops-documents-w-no-heading

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

I chose this Tier 1 issue because the bug is fully contained in a single file, ingestion/chunking/structural_chunker.py, and I was able to trace the exact cause: the _extract_sections method only collects content once a heading has been seen, so a heading-less document silently yields zero chunks. It's a realistic scope for the Week 8–9 window because the fix is localized — collecting content into a default/root section when no heading exists — without needing to understand the wider RAG or ingestion pipeline. There's also an existing test file at tests/unit/test_structural_chunker.py I can follow to add a regression test, giving me a clear before-and-after: a headingless document currently returns [], and after the fix it should return at least one chunk containing the document's text.

## Week 8 - Reproduction & Plan

**Reproduced the bug locally (no Docker needed — the chunker is pure Python):**

Ran the issue's repro snippet against my venv:
```
.venv/bin/python -c "from ingestion.chunking.structural_chunker import StructuralChunker; \
print(len(StructuralChunker().chunk('This is a plain document with no headings at all. ' * 20, {})))"
# observed: 0   (a ~1000-char document produces no chunks)
```

Ran the existing unit test that pins the expected behavior:
```
.venv/bin/python -m pytest tests/unit/test_structural_chunker.py -v
# baseline: 14 passed, 1 failed
# FAILED tests/unit/test_structural_chunker.py::...::test_document_with_no_headings  (assert 0 >= 1)
```

**What reproduction taught me (beyond the issue text):** the same root cause also
silently drops any content that appears *before* the first heading, even in a
document that does have headings — e.g. `Intro line\n# Title\nBody` keeps only
"Body". So the fix needs to handle pre-heading content, not just the all-headingless
case. I also traced the downstream impact: StructuralChunker is the strategy chosen
for `source_type == "readme"` (ingestion/chunking/strategy_selector.py:27), called
from ingestion/pipeline.py, so a plain-text README gets excluded from the RAG index
in production, not just in tests.

**Root cause:** in `_extract_sections`, line 111 only buffers content after a heading
is seen, and line 115 only saves the final section when `heading_stack` is non-empty.
No headings -> empty section list -> `chunk()` returns [].

**Plan:** full details in [PLAN.md](PLAN.md) — chosen approach is to collect
pre-heading / no-heading content into a "root" section inside `_extract_sections`
(fixes both failure modes), with the existing sub-chunking path handling large
heading-less documents for free. Files to change: `structural_chunker.py` and a
regression test in `tests/unit/test_structural_chunker.py`. Definition of done: the
full structural-chunker suite passes 15/15 and `make check` is clean.

## Week 9 - Check-in #1 (mid-week, 2026-08-02): implementation done

**What I built.** Rewrote `_extract_sections` in
`ingestion/chunking/structural_chunker.py` to fix the root cause. Two changes:
(1) content lines are now always buffered instead of only after the first heading is
seen; (2) a small `flush_section()` helper saves the buffered lines whenever a
section closes — including when no heading has been seen yet, which emits a "root"
section with an empty heading path and level 0. I also added an `if content:` guard
so blank stretches between headings no longer produce empty chunks (a small
production-quality improvement, and it keeps the existing empty-section test green).

**Why this approach.** It fixes the bug at the source rather than papering over the
symptom. A fallback like "if the section list is empty, run the semantic chunker on
the whole doc" would satisfy the failing test but would NOT fix content dropped
before the first heading in a document that does have headings. The root-section
approach fixes both, and because `chunk()` already sub-chunks any section over 800
tokens, large heading-less documents get split correctly with no extra code.

**Edge cases handled / verified with new tests:**
- Heading-less document -> at least one chunk, text preserved (`test_no_heading_content_is_preserved`).
- Content before the first heading is kept, not dropped (`test_content_before_first_heading_preserved`).
- Large heading-less document is sub-chunked into multiple chunks, not returned whole (`test_large_document_with_no_headings_sub_chunked`).
- Empty / whitespace-only input still returns `[]` (existing guard untouched).
- Empty sections between headings no longer create empty chunks (existing `test_empty_sections_handled` still passes).

**Verification.**
```
.venv/bin/python -m pytest tests/unit/test_structural_chunker.py -v
# 18 passed  (was 14 passed / 1 failed; the previously-failing
# test_document_with_no_headings now passes, plus 3 new regression tests)
```
Repro now returns 1 chunk instead of 0; `Intro line\n# Title\nBody` now yields both
"Intro line." and "Body." My changed source passes `ruff`; I intentionally did not
run `black` across the file because it would reformat pre-existing `.update({...})`
blocks I never touched — my new code matches the file's existing style.

**Honest status / known limitations (not caused by my change).** The repo has
pre-existing failures unrelated to this issue: ~52 unit tests in other modules
(`test_review_service`, `test_skill_extractor`, `test_tech_detector`, `test_security`)
fail on the branch even with my change stashed, and `mypy` can't run in this
environment due to a Python 3.14 / numpy-stub incompatibility. These are outside the
scope of #149; I confirmed my change doesn't introduce any of them.

**Left for check-in #2:** finalize documentation, self-review the diff against the
project's contribution standards, and open the pull request against
`ascherj/pathreview`.

