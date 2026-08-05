## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings
 #151

 **Issue Selection:**
 I am able to understand what the issue is from the comments in the github issue and can understand what the corrected version is supposed to do (pass the unit tests for bias detection). I was able to find where the issue exists from the tags that say it is in the safety folder and it is inside the bias detector.
 This is my first open source contribution, so I am choosing a tier 1 issue in order to get more experience. I have read the actual code in the file where the issue exists. I have found the unit tests that call on the bias detector so I can understand the context behind how it works and how it is being tested. There are no other students in my session working on this problem but there are a good amount of students in other sections working on it going by the comments in the github issue. This issue should take me somewhere between 4-8 hours to implement by my estimate so I am confident I will be able to test and submit the PR by week 9. I have also verified that this issue has no open blockers or dependencies on other unresolved issues. These meet all the requirements for "Is This Issue Right for Me?"

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In the safety section folder of the project the file **bias_detector.py** uses regex patterns in order to detect phrasing that expresses a certain type of meaning however. The regex patterns are too strict and narrow so it fails to detect bias in 9 units tests. If the regex can be adjusted to pass all the unit tests then the bug will be successfully fixed.

**Branch name:** https://github.com/brtran97/pathreview/tree/fix/151-bias-detector-narrow-patterns

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/brtran97/pathreview/commit/87268077bbfacb5fff7ff842d056fe1203c3c753

**Reproduction summary:**
I reproduced the issue by running the bias detector unit tests in my local
environment with `.venv/bin/python -m pytest tests/unit/test_bias_detector.py -v`
(equivalent to `make test-unit` scoped to this file) or with vscodes pytest GUI. I observed **9 failed, 23
passed**, exactly matching the counts described in issue #151. The failures confirm
that `BiasDetector.detect_bias(...)` returns `(False, '')` for natural phrasings that
should be flagged (e.g. dismissive bootcamp language and age-based assumptions),
because the regex patterns in `safety/bias_detector.py` are too narrow.

The 9 failing tests:

```
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_dismissive_bootcamp_language_detected
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_bootcamp_lacks_rigor_detected
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_demographic_assumption_age_detected
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_coding_bootcamp_variant
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_developer_vs_programmer_distinction
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_multiple_bias_indicators
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_negative_educational_claim
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_rich_poor_assumption
FAILED tests/unit/test_bias_detector.py::TestBiasDetector::test_assumption_vs_observation
========================= 9 failed, 23 passed in 0.18s =========================
```

**PLAN.md link:** https://github.com/brtran97/pathreview/commit/2b00be758a03d6e6a935ee9016aeaa33734eeb6f

**Blockers or open questions:**
None — the failing tests clearly specify the intended behavior, so the path forward is well defined.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md in two iterative commits on
`safety/bias_detector.py`. (1) Broadened `DISMISSIVE_PATTERNS` into an
education-keyword + nearby-negative-predicate structure so natural phrasings
("bootcamp graduates can't write production code", "bootcamp education lacks
fundamentals") match without requiring an exact word sequence — this fixed 7 of the
9 failing tests. (2) Broadened `DEMOGRAPHIC_PATTERNS` to accept plural subjects and
subject anchors beyond "person from" (e.g. "developers from poor backgrounds"),
fixing the remaining 2. All 32 bias-detector tests now pass.

**Next steps:**
Run the full self-review (`make check` / `make test-unit`), open a draft PR into
upstream `ascherj/pathreview`, request peer feedback in Slack, then mark ready for
review and submit.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/615

**PR Body (if it cannot be pulled from link):**
```
## Summary
The bias detector's regex patterns required near-exact phrase sequences, so natural
rephrasings of the same bias slipped through. For example,
`BiasDetector.detect_bias("The candidate only attended a bootcamp, so this project
lacks the rigor of a formal CS education")` returned `(False, '')`. This PR broadens
the patterns in `safety/bias_detector.py` so common phrasings of educational-background
dismissiveness and demographic assumptions are correctly flagged, while positive and
neutral mentions stay unflagged. The `detect_bias()` signature and return shape are
unchanged — only detection coverage improves.

## Issue
Closes #151

## Changes
- Rewrote `DISMISSIVE_PATTERNS` as an education-keyword (`bootcamp` / `coding bootcamp`
  / `self-taught` / `online course`) followed within a bounded window by a negative
  predicate (`can't`, `cannot`, `lacks`, `insufficient`, `inadequate`,
  `not/never equal|comparable`). This removes the previous hard dependency on the exact
  word "is" and on singular-only subjects.
- Broadened `DEMOGRAPHIC_PATTERNS`: age assumptions now accept plural subjects
  ("young developers can't…"), and the socioeconomic-background pattern accepts subjects
  beyond "person from" ("developers from poor backgrounds…").
- Replaced an unbounded `.*` in the origin-based demographic pattern with a bounded
  window to avoid catastrophic backtracking.

## Testing
- [x] Unit tests pass (`make test-unit`) — see note below
- [ ] Integration tests pass (`make test-integration`)
- [x] Linter passes (`make lint`) — on the changed file
- [x] Type checker passes (`make typecheck`) — on the changed file
- [ ] New/updated tests cover the changes (see Notes)

**How to verify manually:**
1. `python -m pytest tests/unit/test_bias_detector.py -v` — 32/32 pass (was 9 failed /
   23 passed before this change; the 9 fixed tests include
   `test_dismissive_bootcamp_language_detected`, `test_demographic_assumption_age_detected`,
   `test_rich_poor_assumption`, `test_assumption_vs_observation`).
2. Spot-check in a REPL:
   - `BiasDetector.detect_bias("bootcamp graduates can't write production code")` → `(True, …)`
   - `BiasDetector.detect_bias("young developers can't handle complex systems")` → `(True, "Demographic assumptions detected")`
   - `BiasDetector.detect_bias("your bootcamp background shows strong fundamentals")` → `(False, "")` (positive mention, correctly not flagged)

## Notes for Reviewers
- **No new tests added** — this PR makes the 9 pre-existing failing tests in
  `tests/unit/test_bias_detector.py` pass; that file already specifies the intended
  coverage, including precision guardrails for positive/neutral phrasings.
- **Pre-existing failures:** the repo has unrelated failing tests in other modules
  (`test_review_service`, `test_skill_extractor`, etc.). This change introduces none —
  the full unit suite went from 53 → 44 failures (my 9 fixes), and no failure is in
  `test_bias_detector.py`.
- **Approach:** kept the existing regex-based design to satisfy the specified tests. A
  more semantic/NLP approach could generalize further but would be a larger change and
  is out of scope here.
```
----------
<br>

**Branch:** `fix/151-bias-detector-narrow-patterns`

**What you built:**
Broadened the regex patterns in `safety/bias_detector.py` so `BiasDetector.detect_bias()`
recognizes common natural phrasings of educational-background dismissiveness and
demographic assumptions — not just near-exact phrase sequences. The `detect_bias()`
signature and return shape (`tuple[bool, str]`) are unchanged; only detection coverage
improved, and positive/neutral mentions of the same topics stay unflagged.

**Tests added or updated:**
No new tests written — the fix targets the 9 pre-existing failing tests in
`tests/unit/test_bias_detector.py`, which now pass (suite is 32/32). Those tests cover:
dismissive educational-background phrasings (bootcamp/self-taught/online-course +
"can't"/"lacks"/"inadequate"/"not equal"), demographic assumptions (age, socioeconomic
background, immigrant/international/foreign developers), and precision guardrails that
positive/neutral mentions (e.g. "your bootcamp background shows strong fundamentals")
remain unflagged.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Note: the repo has pre-existing, unrelated failures in other modules. Verified my
change introduces none: full unit suite went from 53 failed → 44 failed (my 9 fixes),
and `safety/bias_detector.py` passes ruff, black, and mypy cleanly.)

**Draft PR feedback received from:** None


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No code review will not be performed for this summer session

**Summary of feedback:**
No feedback was performed for this session as noted by the course information, but I am preparing myself for how I can respond or address any feed for my PR to make sure that it is accepted and merged into the main project.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
I was suprised by seeing such a large codebase when I first looked at it. It was intimidating at first to see how many parts there was and all the different issues that where available to work on. This was my first time working on a github issue workflow so it also took me some time to get acquainted with the process and the onboarding to find and issue comment on it and perform the fix and make a PR it.

**What did you learn about working in a large codebase?**
[What's different about contributing to someone else's production code
vs. building your own project?]
I learned that it was less important to follow and understand the entire codebase and what every moving part does because it can get overwhelming very quickly. I had to identify where my issue lived and what can be defined as fixing the issue. It was also different to learn about how to follow their documentation like going through their architecture doc to understand the overview of the project and its modules. Then each open source repo should have a contributing.md that details how they want contributions to be done and to follow their format not just write my code freely as I would on my own personal projects.

**How did AI tools help — and where did they fall short?**
AI was most useful to me for exploring the codebase and getting myself orientated when I didn't know where to start. It was also very helpful and suggesting how to fix the issue and what can be done. Where it falls short is defining success and making my own decisions about how to approach the issue and defining the scope of my fix or feature.

**What would you do differently if you started over?**
If I was able to start over I think that I did a good job on this fix I might consider working on a 2nd issue to see what other type of issues exist. My issue was code related but I also saw documentation issues, testing issues, and the tier 2 & 3 problems which are larger and pertain more to the architecture of the codebase where the bug can flow from 1 module to another one.

**What are you most proud of from this module?**
I am proud to have done my first "open-source" contribution. It was my first time working with a large existing codebase like this and using github issues. I know there is still much to learn and my git skills are still a work in progress, but I enjoyed having my first experience working in this format.
