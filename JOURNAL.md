## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This is a safety issue: the bias detector in bias_detector.py uses regex patterns that require near-exact wording, so it misses common natural phrasings of the same bias (dismissive educational-background language; age-based assumptions). The fix needs to broaden the patterns to catch these variations while preserving the detector's intent: flagging genuine bias without over-triggering on neutral text. Success means the 9 currently failing unit tests pass without breaking the 23 that already pass, and that the patterns generalize to catch similarly-phrased bias, not just the exact wording used in the 9 test cases.

**Selection reasoning:**
I chose Tier 1 because, while I've navigated large codebases and fixed
issues before, this is my first time doing so in this kind of simulated
open-source workflow: an actively maintained repo I didn't build, with no
prior context on its structure or conventions, following a PR-based
contribution process. I worked through the "Is this right for me?"
checklist: reproduced the bug locally and confirmed it matches the issue
description, located and read bias_detector.py and its test file
end-to-end, and traced how the current patterns fail against several of the
9 failing tests, for example missing plural word forms and requiring a
fixed word order. I confirmed the fix is scoped to a single file with 9
failing tests that specify the expected behavior. Comment count on the
issue was low with no linked PRs, so collision risk is low, and the
estimated 3–6 hour Tier 1 scope fits comfortably within the Week 8–9
window. I also chose this issue because it fits skills I recently acquired,
and because regex and automated bias detection in text sounded like
interesting topics to explore further in future projects.

**Branch name:** fix/151-bias-detector-narrow-patterns

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/KerolosAssad/pathreview/commit/483621f

**Reproduction summary:**
I ran the exact snippet from the issue description directly in Python and got the same output, (False, ""), confirming the described bug. I then ran the scoped test file (tests/unit/test_bias_detector.py) and the full make test-unit suite, both confirming the same 9 failing tests noted in the issue.

**PLAN.md link:** https://github.com/KerolosAssad/pathreview/blob/fix/151-bias-detector-narrow-patterns/PLAN.md

**Walkthrough video (recommended):** [Loom walkthrough](https://www.loom.com/share/3cbb505daa5d4c10b130428ccba47223)

**Blockers or open questions:**
No blockers, but some of the original designers' intentions are unknown, and the exact way certain patterns should be structured to fix the issue is still uncertain.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed all sub-tasks from PLAN.md for issue #151. Widened DISMISSIVE_PATTERNS and DEMOGRAPHIC_PATTERNS to cover the 9 originally-failing tests (noun/verb form gaps, missing plural forms, word-order variation in the self-taught/university comparison, and a new causal "means" construction). Also fixed two clause-split phrasings quoted directly in the issue's own reproduction steps ("bootcamp... so this project lacks..." and "their age... they likely cannot..."), which weren't covered by the 9 tests alone. While testing the clause-split fix with adversarial inputs, found and fixed a real false-positive risk (an unbounded regex wildcard that could bridge across unrelated sentences), backed by new edge-case tests. Updated PLAN.md's Risks & Unknowns section to document what was confirmed during implementation, including a negation/reported-speech false-positive limitation that was deliberately left unaddressed (documented as a known limitation for the PR).

**Next steps:**
Push the branch, open a draft PR with the template filled in, self-review it, and finalize Check-in 2 with the PR link.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/466

**Branch:** fix/151-bias-detector-narrow-patterns

**What you built:**
Widened the bias detector's regex patterns to catch common natural phrasings the original patterns missed, including plural forms, alternate verb tenses, and bias split across two clauses (e.g. "attended a bootcamp, so this project lacks the rigor..."). All 9 originally-failing tests now pass, plus two additional phrasings quoted directly in the issue that weren't covered by those 9 tests, and a false-positive risk found during adversarial testing was fixed by bounding a regex wildcard. While reviewing the file, also noticed the immigrant/international/foreign pattern is missing "programmers?" (present in every other pattern's noun alternation). Left unfixed: not mentioned in the issue, and no failing test proves it's a real gap.

**Tests added or updated:**
`tests/unit/test_bias_detector.py` — added 4 new tests: `test_clause_split_dismissive_detected` and `test_clause_split_demographic_detected` cover the two clause-split phrasings quoted in the issue's reproduction steps; `test_unrelated_documentation_rigor_not_flagged` and `test_distant_unrelated_system_requirement_not_flagged` are edge-case tests confirming an unrelated trigger and claim in separate sentences no longer incorrectly bridge and get flagged.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

(Introduces no new failures beyond a pre-existing baseline documented in the PR's Notes for Reviewers: 181 pre-existing lint/type errors, 44 pre-existing test failures, none caused by this change.)

**Draft PR feedback received from:** self-reviewed

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No PR review feature exists this term. No feedback was requested or received.

**How you responded:**
N/A – no PR feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Staying precisely scoped to the issue was harder than I expected. It was easy to notice adjacent things worth fixing (a missing noun form in an unrelated pattern, a negation edge case, cross-sentence false positives) and I had to repeatedly decide, deliberately, whether each one was actually in scope or just something I happened to notice while reading the file. Working around pre-existing lint and type-check failures in the codebase was also harder than expected: distinguishing what was genuinely mine to fix from what predated my branch took real care, and figuring out when it was appropriate to bypass pre-commit hooks versus when I should stop and investigate further wasn't obvious at first.

**What did you learn about working in a large codebase?**
The biggest difference from building my own project is the ambiguity around original intent. When I write my own code, I know why I made a design choice. In someone else's codebase, I had to infer intent from existing patterns, conventions, and test coverage, and accept that I'd never be fully certain why the original author drew the lines they did (e.g., why one demographic pattern includes "programmers?" and another doesn't). Working within that uncertainty, rather than resolving it, was a real adjustment.

**How did AI tools help, and where did they fall short?**
AI assistance was most useful for keeping me from overthinking small decisions, for surfacing current conventions and standards through research, and for helping me navigate an unfamiliar problem domain (regex-based bias detection) I hadn't worked with before. It also helped me structure my thinking and stay organized across a long, multi-step process. Where it fell short: it sometimes settled into confirming its own earlier suggestions rather than critically re-examining them, which I had to actively push back on and re-verify myself. It also missed edge cases on its own initiative; the adversarial false-positive tests only happened because I asked for them, not because the AI proactively suggested stress-testing the new patterns before I raised it.

**What would you do differently if you started over?**
I'd ask more questions earlier, particularly about how to handle pre-existing repository issues (broken linting, environment setup quirks) and when using `--no-verify` is appropriate versus when it signals a deeper problem worth investigating. I'd also commit and document more frequently and in smaller increments.

**What are you most proud of from this module?**
I'm most proud of the planning work in PLAN.md and how closely it held up: the risks I predicted before writing any code (negation, overcorrection, pattern maintainability) turned out to be real, and having thought about them in advance meant I recognized them quickly when they actually surfaced during testing, rather than being caught off guard. I'm also proud of catching the false-positive risk in my own new patterns before submitting, through deliberate adversarial testing rather than waiting for a reviewer to find it. Finally, this is my first clean, fully-documented PR in a codebase I didn't build, and completing it end-to-end has made me genuinely more comfortable with the idea of contributing to open source going forward.