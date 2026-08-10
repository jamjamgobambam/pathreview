# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Why this issue fits:**
This is my first contribution to this codebase, so I deliberately looked for a Tier 1
issue rather than something touching the RAG pipeline or agent orchestration I'm not
yet familiar with. Before picking it, I cross-checked the live GitHub issue tracker
(not just the course's static issue list) and found that most other Tier 1 "good
first issue" bugs already had 3-5 competing open PRs from classmates — this one had
none. I also verified the bug myself locally by running
`tests/unit/test_bias_detector.py` rather than trusting the issue title, which
confirmed 9 of 29 tests currently fail. The fix is scoped to a single file
(`safety/bias_detector.py`, a ~40-line class with two regex-pattern lists) with an
existing, thorough test file that already encodes the expected behavior, so I have a
clear, bounded definition of "done" without needing to design new test cases from
scratch — a good match for a first issue where I'm still learning the codebase's
conventions.

**Problem summary:**
`safety/bias_detector.py` flags biased feedback language using a fixed list of regex
patterns for two categories: dismissive comments about educational background (e.g.
bootcamp vs. university) and demographic assumptions (age, immigration status,
socioeconomic background). The patterns only match a handful of rigid phrasings, so
common real-world variations of the same biased statements slip through undetected.
I confirmed this by running the existing test suite: 9 of 29 tests in
`tests/unit/test_bias_detector.py` currently fail, including cases like "self-taught
developers are not equal to university graduates" and "bootcamp attendance means
inadequate training" that should be flagged but aren't. A successful fix broadens the
regex patterns (or replaces them with more flexible matching) so the detector catches
these variations without introducing false positives on neutral/positive feedback,
which the test file already has coverage for. This affects the `safety` module, which
sits between the RAG-generated feedback and what's shown to the end user.

**Branch name:** fix/151-bias-detector-narrow-patterns

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Princy-code/pathreview/commit/df043fc226e657ee4b4da884f6053a7508ca9d70

**Reproduction summary:**
Ran `pytest tests/unit/test_bias_detector.py -v` and confirmed the bug is real and
reproducible: 9 of 29 tests fail because `DISMISSIVE_PATTERNS` and
`DEMOGRAPHIC_PATTERNS` only match a handful of rigid phrasings. For example,
`test_negative_educational_claim` ("self-taught developers are not equal to
university graduates") and `test_assumption_vs_observation` ("bootcamp attendance
means inadequate training") should be flagged as biased but currently return
`False`. Added a `NOTE(#151)` comment in `safety/bias_detector.py` documenting this
so the gap is visible directly in the source, not just in test output.

**PLAN.md link:** https://github.com/Princy-code/pathreview/blob/fix/151-bias-detector-narrow-patterns/PLAN.md

**Walkthrough video (recommended):** Not recorded this week (optional, not graded).

**Blockers or open questions:**
Still deciding whether the fix should stay pure-regex (consistent with the existing
code style) or move to a keyword-proximity helper to avoid regex alternation
becoming unwieldy — will decide in Week 9 based on how many alternations are needed
to cover all 9 failing cases without introducing false positives on the 23 passing
"not flagged" tests.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from `PLAN.md`: broadened `DISMISSIVE_PATTERNS` and
`DEMOGRAPHIC_PATTERNS` in `safety/bias_detector.py` to accept the phrasing
variations the existing test suite expects (e.g. plural nouns like "developers",
extra connecting words like "means", "are" instead of "is", and "developers from"
in addition to "person from"). Went with the pure-regex approach from `PLAN.md`
rather than a keyword-proximity helper — the alternation stayed small enough (a
handful of extra alternatives per pattern) that a rewrite wasn't justified.

**Next steps:**
Run the full self-review (`make check`, `make test-unit`), confirm no regressions
outside `test_bias_detector.py`, and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/749

**Branch:** fix/151-bias-detector-narrow-patterns

**What you built:**
Broadened the regex patterns in `safety/bias_detector.py`'s `BiasDetector` class so
`detect_bias()` catches common phrasing variations of dismissive educational
comments and demographic assumptions (different verbs like "means"/"lacks",
plural nouns, reordered subject/verb structure) instead of only a handful of exact
phrase templates. The function's signature and return contract are unchanged.

**Tests added or updated:**
No new tests — `tests/unit/test_bias_detector.py` already encoded the intended
behavior (that's how I verified the bug in Week 8). All 32 tests in that file now
pass; previously 9 failed. Confirmed the fix didn't introduce false positives on
the file's 12+ "not flagged" tests covering neutral/positive feedback.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Note: the repo has pre-existing failures unrelated to this change — 181 ruff
errors repo-wide and 44 failing tests in other modules, e.g.
`test_review_service.py`, `test_skill_extractor.py`, `test_tech_detector.py`,
tied to other open issues classmates are fixing. `safety/bias_detector.py` itself
is clean: ruff, black, and mypy all pass with zero errors, and
`tests/unit/test_bias_detector.py` is 32/32 passing. Confirmed via
`pytest tests/unit -m unit -q` before and after my change that this PR introduces
no new failures.)

**Draft PR feedback received from:** none — submitting under today's deadline
without time for a peer review cycle.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback — reviewer feedback isn't provided this term (Su26). PR #749 shows
"No reviews" as of this writing.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Trusting the course's static issue list less than I expected to. Most of the
listed "good first issue" bugs I initially considered already had 3-5 open PRs
from classmates when I checked the live GitHub tracker — the static list didn't
reflect that. I also underestimated how much care broadening a regex takes: my
first instinct was to just make patterns match more, but every widened pattern
had to be re-checked against a dozen tests that were deliberately written to
*not* trigger, so the actual difficulty was balancing catching more phrasings
against not flagging neutral feedback, not the regex syntax itself.

**What did you learn about working in a large codebase?**
That an existing, well-written test file functions as the real specification —
I never wrote a single new test for `test_bias_detector.py`; my job was making
`bias_detector.py` satisfy behavior the maintainers had already encoded in 29
test cases. That's different from a personal project, where I'd usually write
the test alongside the code. It also meant I could verify a bug was real (or
already fixed) just by running the suite, rather than trusting an issue title.

**How did AI tools help — and where did they fall short?**
AI was most useful for the unglamorous verification work: cross-referencing the
live GitHub issue tracker against the local issue manifest, running the test
suite to confirm the bug before committing to it, and reasoning through which
regex changes would introduce false positives against the full test file. It
fell short anywhere that required my own identity or judgment — claiming the
issue with a comment, deciding between two uncontested issues, git commits and
pushes, and opening the actual PR all had to be done by me, by design.

**What would you do differently if you started over?**
I'd check the live issue tracker for open competing PRs *before* reading the
course's static issue list at all, instead of finding a candidate first and
then discovering it was already claimed. I'd also set up Docker earlier in
Week 7 — it needed an interactive `sudo` password partway through the install,
which I didn't expect and which cost time I could have used elsewhere.

**What are you most proud of?**
Catching that several "easy" issues were stale before committing to one, and
independently confirming the bug via the test suite instead of trusting the
issue description. That gave me a genuinely unclaimed, well-scoped issue and a
verified fix (32/32 tests passing, no regressions) rather than one I'd have had
to abandon partway through after finding out it was already someone else's PR.
