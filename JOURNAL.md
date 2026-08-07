# Module 3 Journal for PathReview

A running record of my Module 3 contribution work. A new section is added each week.

---

## Week 7 Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/64

**Issue title:** Prompt injection defense doesn't sanitize newline characters in user-supplied resume text

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
PathReview feeds user-supplied resume text into LLM prompts, and `safety/prompt_defense.py`
is the guardrail meant to neutralize injection attempts before that happens. Its `sanitize()`
method only strips template/markup delimiters (`{{ }}`, `{% %}`, `<`, `>`) and never touches
newline-based attacks, so a resume containing a line break followed by `---` or `System:` can
terminate the system prompt and smuggle in new instructions, and `sanitize()` passes it through
untouched. The interesting wrinkle I found reading the code is that the sibling method
`is_injection_attempt()` *already detects* these newline and role-switch patterns via regex, so the
module clearly knows they are dangerous. The sanitizer just does not act on them (and the detection
regex itself misses spacing variants like `System  :`, which is why one existing test in that module
is already failing). A successful fix makes resume text safe to embed in a prompt regardless of
newline tricks, covered by tests that inject these payloads and assert they are stripped or flagged.

**Branch name:** `fix/64-sanitize-newline-injection`

**Setup confirmation:** [x] App runs locally at localhost:5173
> Frontend (Vite dev server) confirmed loading at http://localhost:5173, `HTTP 200`, page title
> "PathReview - AI Portfolio Review Assistant". Python deps installed into a local `.venv`
> (`pip install -e ".[dev]"`) and the unit test suite runs. Note that Docker was not available in my
> environment, so the Postgres/Redis/Chroma backing services and the FastAPI backend were not
> brought up. The `localhost:5173` frontend loads independently of them.

**Cohort ledger:** [x] Issue added to cohort ledger
> Claimed on the GitHub issue thread (commented as MyviordDjaja, AI201 section 2a) and recorded on
> my section's tab of the cohort issue ledger (name / GitHub username / issue #64).

---

### Selection notes on "Is this right for me?"

- **Scope is tight and well-defined.** The issue names exactly one file (`safety/prompt_defense.py`)
  and the exact patterns being missed (`\n---\n`, `\nSystem:`). I'm not guessing at acceptance
  criteria. The behavior to fix is spelled out.
- **It's verifiable, not cosmetic.** This is a security bug, so success is testable in a way that's
  hard to fake. I can write a test that injects the payload and assert it doesn't survive `sanitize()`.
  There's already a `tests/unit/test_prompt_defense.py` I can extend, and it currently has 31 passing
  / 1 failing test, a concrete baseline to work against.
- **Right difficulty.** Tier-2 (est. 4 to 6 hrs) means a real fix rather than a typo, but it's a single
  module and not a multi-file architectural change I'd still be untangling next week.
- **Skills match.** It's Python plus regex plus a clear input/output contract, squarely within what I can
  do without needing the full backend stack running.
- **Known caveat (being honest).** The issue is crowded. Several people (including a TF, `mdoran3`)
  have commented claiming it, though no one has an open PR yet. I'm proceeding because it's still
  open and unclaimed by any PR, and I'd rather do a real security fix and risk being scooped than
  pick something trivial. Flagging this for standup so the cohort can decide how to handle duplicate
  claims.

### Environment and setup notes

- Forked `ascherj/pathreview`, cloned my fork (`MyviordDjaja/pathreview`), added `upstream` remote.
- Created `.venv` and installed dev dependencies (`pip install -e ".[dev]"`) on Python 3.14.
- Ran the unit suite and got **375 passed / 53 failed** overall, which is expected, since this course
  repo is intentionally seeded with the bugs the tracker issues describe (each tier issue is roughly
  one failing test).
- Frontend confirmed at `localhost:5173` (see Setup confirmation above).
- Docker/Compose was not installed in my environment, so the Postgres plus Redis plus Chroma services
  and the FastAPI backend were not started this week. Not a blocker for issue #64, whose fix and tests
  live entirely in the `safety` module and run under `pytest` without those services.

---

## Week 8 Reproduction and solution planning

**Reproduction commit link:** https://github.com/MyviordDjaja/pathreview/commit/47a15e10b74f9ac6db8f04560eb8169b5b0be2d4

**Reproduction summary:**
I reproduced the bug with a failing unit test file, `tests/unit/test_prompt_defense_newline_repro.py`,
that runs the documented injection payloads through `PromptDefense.sanitize()`. The tests assert the
`\nSystem:` role-switch and `\n---\n` separator patterns are neutralized. All three fail against
current code (the payloads pass through untouched, and `is_injection_attempt()` still fires on the
sanitized output), confirming the issue is real and lives in `safety/prompt_defense.py`.

**PLAN.md link:** https://github.com/MyviordDjaja/pathreview/blob/fix/64-sanitize-newline-injection/PLAN.md

**Walkthrough video (recommended):** not recorded

**Blockers or open questions:**
- Design choice for the fix is whether to strip the newline markers or escape and de-anchor them
  (break the line boundary without deleting content). No non-test code currently calls `PromptDefense`,
  so there's no downstream consumer constraining the exact output, and I'll keep the transformation
  minimal.
- Whether to also fix the related detection gap (`System  :` with spaces before the colon, the
  existing failing `test_whitespace_variations_detected`) within this issue's scope. Leaning yes,
  since it's the same module and the same newline theme.

---

## Week 9 Solution building and PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `safety/prompt_defense.py` iteratively, following PLAN.md, across three commits.
- `refactor:` extracted the injection regexes into shared module-level constants so `sanitize()`
  and `is_injection_attempt()` use one source of truth (PLAN sub-task 1). Behavior-neutral.
- `fix:` `sanitize()` now collapses separator lines (`\n---\n`) and de-anchors role-switch and
  instruction markers (`\nSystem:`, `\nIgnore`) by turning the leading newline into a space, and the
  role-switch detection regex was loosened to catch `System  :` (PLAN sub-tasks 2 and 3).
- `test:` added sanitize-neutralization, idempotency, clean-resume-preserved, multi-payload,
  spaced-colon detection, and a ReDoS-guard test to the canonical `test_prompt_defense.py` (sub-task 4).

All four in-scope tests (the 3 Week-8 reproduction tests plus the pre-existing `test_whitespace_variations_detected`)
now pass, and the design chose de-anchoring over deletion to avoid mangling legitimate resumes.

**Next steps:**
Confirm no regressions across the full unit suite (sub-task 5), write the PR description against the
repo template, open a draft PR, and request peer feedback before marking it ready.

**Blockers:**
None. (Docker still unavailable locally, but this change needs no backing services, and the `safety`
module runs under `pytest` without them.)

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/737

**Branch:** `fix/64-sanitize-newline-injection`

**What you built:**
`PromptDefense.sanitize()` now neutralizes newline-based prompt injection. It collapses `\n---\n`
separator lines and de-anchors `\nSystem:`-style role-switch and instruction-override markers so a
line break can no longer forge a prompt boundary, while preserving legitimate content and ordinary
paragraph newlines. The detect and sanitize sides now share one set of pattern constants, and the
role-switch detector was tightened to catch `System  :`.

**Tests added or updated:**
`tests/unit/test_prompt_defense.py` gained 7 tests covering sanitize neutralization, idempotency,
clean-resume preservation, multi-payload handling, spaced-colon detection, and regex-backtracking
safety. The Week-8 reproduction file `tests/unit/test_prompt_defense_newline_repro.py` now passes
unchanged.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
> Under the documented pre-existing-failures rule, "passes" means my change introduces **no new**
> failures. Baseline `make test-unit` was 56 failed / 375 passed, then 52 failed / 379 passed after
> (the 4-test delta is exactly my in-scope tests, and no `safety` tests fail). `make lint` and
> `make typecheck` have pre-existing repo-wide errors. My two files are clean except one pre-existing
> `F841` in `test_code_blocks_handled` that predates this issue. Documented in the PR's Notes for
> Reviewers.

**Draft PR feedback received from:** none

---

## Week 10 Iteration and reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No, still awaiting review

**Summary of feedback:**
N/A

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
The design decision, not the code. I expected the hard part of a regex bug to be the regex, but the
regexes took an afternoon and the question of what `sanitize()` should do with a match took longer.
Stripping the payload outright would mangle a legitimate resume that happens to contain a `---`
divider or the word "System", so I landed on de-anchoring (turning the leading newline into a space
so the marker can no longer forge a line boundary) instead of deletion. Nothing in the issue told me
which was right, and no non-test code even calls `PromptDefense`, so I had to infer the contract from
the module's own docstrings and tests and then defend the choice in the PR. The other surprise was
how much work "the tests pass" turned out to be in a repo that intentionally ships with 50-plus
pre-existing failures. Proving my change was clean meant recording a baseline (56 failed / 375
passed), rerunning after (52 failed / 379 passed), and showing the delta was exactly my in-scope
tests. 

**What did you learn about working in a large codebase?**
That the codebase already contains most of the answer if you read it before writing anything. The
key insight of my whole fix came from noticing that `is_injection_attempt()` already detected the
exact patterns `sanitize()` ignored, which turned the fix from "invent a defense" into "make two
sibling methods share one source of truth". In my own projects I would have just written new code.
Here the right move was a behavior-neutral refactor first (extract the shared pattern constants) and
the fix second, in separate commits, so a reviewer can see that the risky change is small. I also
learned that in someone else's production code you spend real effort on things that are invisible in
a solo project, like not widening scope (I almost pulled in a second detection gap and had to justify
why it belonged), matching the existing test file's style, and writing the PR for a maintainer who
has never met me and will not sit through an explanation.

**How did AI tools help, and where did they fall short?**
AI was most useful as a fast reader and a skeptical test partner. It traced the module and its 32
existing tests quickly, helped me enumerate payload variants I would not have thought to try
(`System  :` with spaces, multi-payload inputs, idempotency, a ReDoS guard on the new regexes), and
caught small inconsistencies in my own journal, like a wrong added-test count. It fell short on
judgment calls. It could lay out strip versus de-anchor as options but the choice, and owning the
tradeoff in the PR, was mine. It also could not verify anything for real. Every "the tests should
pass now" claim still had to be run against the actual suite, and the baseline-delta accounting for
the pre-existing failures was something I had to define myself because the AI's default framing of
"passing" did not fit this repo. AI accelerated the mechanical 70 percent and the remaining 30
percent was exactly the part that needed a human.

**What would you do differently if you started over?**
I would get Docker working in week one rather than deciding it was not a blocker. It happened
to be true for this issue, but if my fix had touched the API layer I would have lost
days mid-module standing up the backing services under deadline pressure.

**What are you most proud of from this module?**
The reproduction commit. Before writing any fix I committed a failing test file that ran the
documented payloads through `sanitize()` and proved the hole existed, and that one artifact carried
the whole module. It forced me to understand the bug precisely, it defined "done" before I was
attached to a solution, and by the end it became the acceptance test that passed unchanged against
the final code. It is the first time I have really worked test-first on something adversarial, where
the test is an attack, and it changed how I want to approach security-flavored work from now on.
