# Project journal

## Week 7 - Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The checker requires two matching non-stopword terms, so a short claim such as
`Knows Python` cannot be supported even when Python appears in the retrieved context.
The work is centered on `rag/evaluator/faithfulness_checker.py` and its unit tests. I
also included the related `text=None` failure from #153 at this checker's input
boundary, without claiming the separate suite-level path is fixed.

**Branch name:** `fix/152-faithfulness-short-claims`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

### Is this right for me?

- This is a Tier 1 change isolated to one evaluator and its tests.
- The issue provides a concrete input and expected score that can be reproduced first.
- Existing faithfulness tests provide a clear before-and-after target.
- General natural-language inference remains outside the scope of this lexical
  checker.

## Week 8 - Reproduction and solution planning

**Planning record commit:**
[d907e28](https://github.com/ahmedtaha100/pathreview/commit/d907e28083e80d84f5d5a9a308dd373eac4e7281)

**Failing reproduction commit:**
[1eb292b](https://github.com/ahmedtaha100/pathreview/commit/1eb292b3d11455a0f1995010d7334d637507450c)

**Reproduction summary:**
The exact `Knows Python. Knows SQL.` example returned `0.0` despite both facts being
present. Passing `{"text": None}` directly to `FaithfulnessChecker.check()` also
raised `TypeError`. At the reproduction commit, the two focused regression tests fail
for those reasons before the implementation is applied.

**PLAN.md:**
[Solution plan](https://github.com/ahmedtaha100/pathreview/blob/fix/152-faithfulness-short-claims/PLAN.md)

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:**
The checker compares terms rather than meaning, so negation and entity attribution
remain known limitations. The repository also has unrelated baseline check failures,
which require a same-environment comparison.

**Working branch:**
[fix/152-faithfulness-short-claims](https://github.com/ahmedtaha100/pathreview/tree/fix/152-faithfulness-short-claims)

## Week 9 - Solution building and PR submission

### Check-in 1 (mid-week)

**Current progress:**
The exact #152 and checker-level #153 failures are reproduced. The implementation now
extracts narrowly reporter-led short claims, preserves the ordinary two-term support
rule, and skips malformed context text. Focused regression coverage is in place.

**Next steps:**
Run false-positive and technical-identifier probes, compare the complete unit failure
set with a fresh `main` worktree, finish the contribution checks, and make the PR
description match only the verified behavior.

**Blockers:**
The repository has unrelated unit, lint, formatting, and type-check failures on
`main`, so verification must use the course's documented no-new-failures process.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/211

**Branch:** `fix/152-faithfulness-short-claims`

**What you built:**
I updated the faithfulness checker so one-fact claims are scoreable only after a narrow
reporting verb such as `knows`. Ordinary claims keep the original two-term support
threshold, partial evidence receives proportional credit below that threshold, and
malformed context text is skipped without hiding valid sibling chunks.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` now covers the exact #152 reproduction, the
checker boundary from #153, supported and unrelated short claims, subject stripping,
the ten-claim cap, partial scores, punctuation, PascalCase dotted names, common
technical identifiers, and Unicode apostrophe and in-word hyphen variants. The
focused run passes all 55 collected cases with warnings treated as errors, reaching
100% checker coverage (86/86 statements and 28/28 branches).

The `make test-unit` equivalent reports `412 passed / 49 failed`, compared with
`375 passed / 53 failed` on a fresh same-environment `main`
worktree. The four original faithfulness failures now pass, and the remaining 49
failure node IDs are identical on both revisions.

**Self-review confirmation:** [x] `make check` passes*  [x] `make test-unit` passes*

\* GNU Make is unavailable in this Windows environment, so I ran each Makefile command
directly. Under the course's pre-existing-failure policy, these boxes mean the change
adds no failure: Ruff reports 180 existing errors versus 182 on `main`; Black
`--check` reports 50 files versus 52; and mypy reports the same 103 errors in 26 files
on both. Both changed Python files pass Ruff and Black, and the checker passes strict
mypy. Integration collection exits 5 with no tests on both revisions.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — no review arrived

**Summary of feedback:** The Summer 2026 project instructions state that reviewer
feedback is not provided for this iteration of the course. I also checked PR #211 on
August 9, 2026; it has no conversation comments, inline review comments, submitted
reviews, requested changes, or review threads.

**How you responded:** Not applicable — no reviewer feedback was received, so there was
no response or reviewer-requested change to make. If maintainer feedback arrives later,
I will document the comment, my decision, the change or explanation I provided, and the
verification result within the repository's 48-hour response window.

---

### Reflection

**What was harder than you expected?**

The hardest part was not reproducing #152; it was defining a fix narrow enough to avoid
creating false support elsewhere. The obvious rule — let one matching word count — made
`Knows Python` work, but could also make an ordinary claim such as `Python expert` look
supported by context that mentioned only Python. I had to preserve the normal two-term
threshold while recognizing only a specific reporter-led one-fact form in
`rag/evaluator/faithfulness_checker.py`.

The repository's inherited failures also made verification harder than a normal green
test run. Instead of relying on totals, I compared the exact failing test node IDs on the
branch and the same-environment baseline. That proved the four original faithfulness
failures were repaired without replacing them with different failures elsewhere.

**What did you learn about working in a large codebase?**

I learned that contributing to someone else's codebase means treating existing behavior,
tests, contribution rules, and module boundaries as contracts. Before changing the
checker, I had to read `docs/CONTRIBUTING.md`, follow the repository's branch and commit
conventions, study the existing unit tests, and understand how the checker fits into the
larger RAG evaluation path.

Scope mattered as much as implementation. The change safely handles `text=None` at the
`FaithfulnessChecker.check()` boundary, but `RelevanceScorer.score()` can still reject
that input earlier inside `EvalSuite.run()`. Naming that boundary honestly was better
than claiming the related issue was fixed everywhere.

**How did AI tools help — and where did they fall short?**

AI coding tools helped me navigate an unfamiliar repository, form debugging hypotheses,
and generate adversarial tests for punctuation, technical identifiers, malformed context
chunks, Unicode variants, and the claim limit. They were most useful as a fast source of
questions to investigate, especially when a small parser rule had effects I did not see
immediately.

They fell short when suggestions treated the lexical checker like a general language
understanding system. Several broader ideas involving stop words, negation, or semantic
rules changed unrelated behavior or created new false positives. I had to reject or
rework those suggestions and use executable regressions, coverage, style/type checks,
and an exact branch-versus-baseline comparison as the evidence for each final decision.

**What would you do differently if you started over?**

I would write the acceptance matrix before changing the scorer. It would include the
positive issue example, unrelated one-word controls, material mismatches, partial
evidence, malformed inputs, technical identifiers, and the first-ten-claims behavior
from the beginning. I would also capture the baseline failure IDs immediately instead of
first relying on pass/fail totals.

I would follow the course's literal six-section PLAN structure and keep the draft PR open
long enough to request peer or mentor feedback before marking it ready. I would also
publish the midweek check-in at the actual midpoint instead of adding both entries in the
final Sunday journal commit. Those process improvements would make the work easier to
review and the course record stronger, even though the implementation itself would stay
narrow.

The Week 9 course feedback also called out how the reporting-verb, subject-stripping,
role-noun, and technical-identifier rules interact. I would respond by splitting those
concerns into smaller helpers and adding short why-comments around non-obvious branches,
so a future maintainer would not need to reverse-engineer the intent from all 55 tests.

**What are you most proud of from this module?**

I am most proud that the final PR fixes the exact `Knows Python. Knows SQL.` failure while
keeping unrelated one-word feedback unscoreable. The submitted checker reaches 100%
statement and branch coverage, and the full-suite comparison shows the same 49 inherited
failure identities rather than introducing a new one.

I am also proud that the contribution states its limits clearly. It preserves technical
identifiers such as `C++`, `.NET`, and `Node.js`, handles malformed sibling chunks, and
does not pretend lexical overlap can solve negation, contradiction, or entity
attribution. That combination of a useful fix, reproducible evidence, and honest scope is
the part of the module I would be most comfortable explaining to a maintainer or
interviewer.
