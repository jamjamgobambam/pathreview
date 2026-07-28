# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The RAG faithfulness checker scores how well generated feedback is grounded in the
retrieved context by breaking the feedback into claims and checking each one for
support. The bug is in how "supported" is decided: `_is_supported` counts how many
meaningful (non-stop-word) words a claim shares with the context and requires an
*absolute* minimum of two overlapping words. That threshold does not scale with
claim length — a short but valid claim that contains only one meaningful token (for
example "Uses Kubernetes", where only "kubernetes" survives stop-word filtering)
can never reach two overlaps, so it is always scored as unsupported even when the
context matches it perfectly. This lives in the `rag` module
(`rag/evaluator/faithfulness_checker.py`). A successful fix replaces the fixed
`>= 2` cutoff with a length-aware rule (e.g. a required overlap that scales with the
number of meaningful tokens in the claim), so genuinely-supported short claims are
correctly credited and the overall faithfulness score stops being biased downward by
short sentences.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this issue right for me?" checklist reasoning

**Part 1 — Understanding the issue**
- In my own words: the checker marks a claim "supported" only when it shares at
  least two non-stop-word tokens with the context. Short claims can carry only one
  meaningful token, so they can never clear that bar — they're always counted as
  unsupported, dragging the faithfulness score down.
- Affected area: the `rag` module, specifically
  `rag/evaluator/faithfulness_checker.py`. I located and read the file.
- "Done" looks like: a short, genuinely-grounded claim (single meaningful token that
  appears in the context) is scored as supported, and the existing multi-word
  behavior is unchanged. I'll add a unit test that fails today (a short supported
  claim scoring 0.0) and passes after the fix.

**Part 2 — Tier fit**
- Tagged Tier 1 (starter / good first issue). The change is one static method in one
  file. This matches my level; I'm choosing a well-scoped Tier 1.

**Part 3 — Codebase readiness**
- I read the specific method `_is_supported` (lines 66-88) and confirmed the root
  cause is the hardcoded `return len(meaningful_overlap) >= 2` on line 88, combined
  with stop-word filtering that can strip a short claim down to a single token.
- I read the surrounding class: `check()` computes `supported / len(claims)`, and
  `_extract_claims()` already drops sentences of length <= 10 chars, so the fix must
  be careful to reason about what a "claim" can look like after extraction.
- I read the test file `tests/unit/test_faithfulness_checker.py`. Existing tests
  like `test_minimum_overlap_required` and `test_common_words_filtered_in_overlap`
  call `_is_supported` but don't assert on its boolean result, so the short-claim
  behavior isn't pinned yet — I'll add an assertion-bearing test.

**Part 4 — Scope and time**
- Estimated effort: a few hours (single-method threshold change + a new test, plus a
  quick check that the existing tests still pass). Realistic for Weeks 8-9.
- No blockers or dependencies listed on the issue.
- Checked crowding on the tracker/ledger and I'm comfortable proceeding (claims are
  non-exclusive; grading is on my own artifacts).

---

### Codebase map (files most relevant to this issue)

- `rag/evaluator/faithfulness_checker.py` — the class being fixed. `check()` is the
  entry point (extract claims → concatenate context → score each claim);
  `_is_supported()` holds the buggy threshold; `_extract_claims()` decides what
  counts as a claim.
- `tests/unit/test_faithfulness_checker.py` — existing test suite; I'll extend it
  with a failing-then-passing short-claim test.

**Planned fix (high level, for Week 8):** make the support decision length-aware
instead of a fixed `>= 2`. Candidate approaches: require
`len(meaningful_overlap) >= min(2, len(claim_meaningful_tokens))`, or switch to an
overlap ratio (e.g. a fraction of the claim's meaningful tokens must appear in the
context). Pick whichever keeps existing multi-word tests green while letting a
fully-grounded single-token claim count as supported. Add a regression test for the
short-claim case.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** _https://github.com/tureh1/pathreview/commit/04c863c7862b2dab218b6231c17fbf560ce5412d

**Reproduction summary:**
I reproduced the bug two ways. Running `_is_supported("Is scalable", "The architecture
is scalable and well-tested.")` returns `False` even though "scalable" appears verbatim
in the context, and `check("Is scalable.", [grounded context])` returns `0.0`. The same
wording as a longer claim scores `1.0`, which proves the score depends on claim length,
not on whether the claim is grounded. I captured this as two failing unit tests in
`tests/unit/test_faithfulness_checker.py`
(`test_short_grounded_claim_is_supported_issue_152` and
`test_check_scores_grounded_short_feedback_above_zero_issue_152`).

**PLAN.md link:**
https://github.com/tureh1/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md

**Walkthrough video (recommended):** _<optional Loom link, ≤2 min — not graded>_

**Blockers or open questions:**
- Undecided between `min(2, meaningful_token_count)` and a ratio-based threshold; I'll
  pick whichever fixes the short-claim tests without flipping
  `test_feedback_with_no_support_in_context` / `test_is_supported_without_keywords`.
- While reproducing, I found 4 pre-existing failures in this test file. Three
  (`test_partial_support_returns_middle_score`, `test_multiple_context_chunks`,
  `test_multiple_claims_varying_support`) stem from the same `>= 2` threshold and/or a
  separate punctuation-tokenization weakness; one (`test_none_context_chunk_text`) is a
  `TypeError` that belongs to issue #153, not #152, so it is out of scope here.
