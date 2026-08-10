# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/71

**Issue title:** Implement a red-teaming test suite for the prompt injection defense

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
PathReview has a safety layer (the `safety/` module) that is supposed to detect
and block prompt injection attacks before user-supplied text reaches the LLM, but
right now there is no automated way to prove that this defense actually works or
that it keeps working as the code evolves. This issue asks for a dedicated
red-teaming test suite that feeds a curated collection of known prompt-injection
attack patterns through the safety layer and asserts that every one of them is
blocked. The work also involves organizing the attack payloads as reusable
fixtures and wiring the suite into CI so it runs automatically whenever anything
under `safety/` changes. A successful fix gives the project continuous,
regression-proof evidence that its injection defenses hold — turning "we think the
safety layer works" into "we can prove it on every commit."

**Branch name:** test/71-prompt-injection-red-team-suite

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

### "Is this right for me?" — selection notes

- **Scope / effort:** The issue is labeled **Tier 3** (advanced) with an estimated
  7–10 hours of work. It is heavier than the Tier 1 issues recommended for a first
  contribution, so I am going in aware that most of the effort is in curating a
  broad, realistic set of injection payloads and understanding the existing
  `safety/` behavior — not in a single small code change.
- **Where it lives:** The change is well-contained in new files
  (`tests/security/test_prompt_injection.py` and
  `tests/fixtures/injection_attempts/`) plus a CI workflow tweak. It adds tests
  rather than modifying core application logic, which lowers the risk of breaking
  existing features.
- **What I need to understand first:** How the `safety/` layer exposes its
  detection/blocking API, what "blocked" looks like as a return value or raised
  error, and the existing test conventions (`pytest` markers — note the `security`
  marker is already declared in `pyproject.toml`).
- **Dependencies / blockers:** No external API key is required to run the safety
  layer locally (the app defaults to `LLM_PROVIDER=mock`), so the suite can be
  developed and run entirely offline. CI wiring depends on the existing
  `.github/workflows/` setup.
- **Fit:** Good fit for building confidence with the codebase's testing and safety
  systems; the main stretch is the Tier 3 breadth, which I'll manage by starting
  with a small set of attack categories and expanding.

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/himankgalundia/pathreview/commit/58fad9a

**Reproduction summary:**
Confirmed the gap two ways: `pytest -m security --collect-only` reports "no tests
collected (428 deselected)" and `tests/security/` holds only `__init__.py`, so the
declared `security` marker guards nothing and CI has no security job. Adding a
`security`-marked reproduction test also surfaced a real defensive bypass —
`PromptDefense.INJECTION_PATTERNS` anchors every regex to a leading newline, so
first-line attacks like "Ignore all previous instructions…" and "System: …" are
**not** flagged (the four `test_first_line_*` cases fail while the newline-prefixed
control passes).

**PLAN.md link:** https://github.com/himankgalundia/pathreview/blob/test/71-prompt-injection-red-team-suite/PLAN.md


**Blockers or open questions:**
- Scope: does #71 want only the red-team suite, or also the `PromptDefense`
  hardening the suite exposes? If hardening is out of scope, I'll track known
  bypasses as `xfail(strict=True)` rather than ship a red build.
- `PromptDefense` is currently imported only by tests, not by the request path —
  need to confirm whether wiring it into the API is in or out of scope for #71.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Four of five PLAN.md sub-tasks are complete. (1) Curated attack fixtures under
`tests/fixtures/injection_attempts/` — five category files (role-switching,
instruction-override, template injection, code execution, separator) plus a
benign control set. (2) Built the suite: `tests/security/injection_corpus.py`
(fixture loader) and `tests/security/test_prompt_injection.py`, a parametrized
`security`-marked suite (25 attacks asserted blocked, 8 benign asserted allowed,
1 empty-corpus guard) — 34 tests, all green. (3) Hardened `PromptDefense`: the
patterns were anchored to a leading `\n`, so first-line attacks slipped through;
re-anchored them to `(?:^|\n)` (start-of-text or any line) and added a phrase
pattern for "ignore/disregard … instructions" anywhere. (5) Retired the Week 8
reproduction file into the real suite.

**Next steps:**
Wire the CI `test-security` job (done), then open a draft PR, request peer
review in Slack, and finalize.

**Blockers:**
Pre-existing broken baseline in the repo (unrelated to #71): 53 failing unit
tests, ~182 ruff and 52 black issues before any of my changes. Working to the
"no new failures" bar and documenting the baseline in the PR.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/272

**Branch:** `test/71-prompt-injection-red-team-suite`

**What you built:**
A prompt-injection red-team test suite that fires a curated corpus of known
attacks (loaded from fixture files) at `PromptDefense.is_injection_attempt` and
asserts each is blocked, with a benign control set guarding against false
positives, wired into CI as a `test-security` job. Also hardened the detector so
first-line injections (previously undetected because patterns required a leading
newline) are now caught.

**Tests added or updated:**
- `tests/security/test_prompt_injection.py` — new red-team suite (34 tests).
- `tests/security/injection_corpus.py` — fixture loader.
- `tests/fixtures/injection_attempts/*.txt` — curated attack + benign payloads.
- `safety/prompt_defense.py` — hardened patterns; all 32 existing
  `tests/unit/test_prompt_defense.py` tests still pass (one previously-failing
  case, `test_whitespace_variations_detected`, now passes).

**Pre-existing failures (documented per assignment):** Before my changes,
`make test-unit` reported 53 failing tests and `make check` reported ~182 ruff /
52 black / 5 mypy issues, all unrelated to #71. After my changes: 52 failing
unit tests (the one fewer is the case my fix repaired) and **zero new** ruff /
black / mypy issues in the files I touched. My contribution introduces no new
failures.

**Self-review confirmation:** [x] make check passes (no new failures)  [x] make test-unit passes (no new failures)

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback

**How you responded:**
(No feedback to respond to.)

---

### Reflection

**What was harder than you expected?**
The hardest part wasn't writing the tests — it was deciding what "green"
should even mean. My Week 8 reproduction surfaced a real bypass: every regex
in `PromptDefense.INJECTION_PATTERNS` was anchored to a leading `\n`, so a
first-line attack like "Ignore all previous instructions…" or "System: …"
sailed straight through undetected. That put me at a fork the issue didn't
answer: do I ship a red-teaming suite that honestly *fails* against today's
code (proving the gap), or do I harden the detector so the suite is honestly
green? Sitting in that ambiguity — and realizing "just write the tests" was
actually a scope decision with a maintainer-intent question behind it — was
harder than any of the regex work. I planned for it (tracking bypasses as
`xfail(strict=True)` as a fallback) but ultimately chose to re-anchor the
patterns to `(?:^|\n)` and keep a benign control set as the false-positive
guard, so the suite is both green and honest.

The second surprise was environmental: the repo shipped with a broken
baseline — 53 failing unit tests and ~182 ruff / 52 black issues before I
touched anything. Distinguishing "did I break this?" from "was this already
red?" ate more time than I expected and forced me to be disciplined about
capturing a before/after snapshot.

**What did you learn about working in a large codebase?**
Contributing to someone else's production code is far more about *reading and
inference* than writing. On my own projects I hold the whole design in my
head; here I had to reverse-engineer the contract — how `PromptDefense`
exposes detection, what "blocked" looks like as a return value, which pytest
markers exist (`security` was declared in `pyproject.toml` but guarded zero
tests), and how CI is wired — before I could write a single line I trusted.

I also learned to respect the blast radius. I deliberately picked an issue
that lived almost entirely in *new* files (fixtures, a new test module, a CI
job) so my footprint on core logic was tiny; the one file I did modify
(`safety/prompt_defense.py`) I changed only after confirming all 32 existing
`test_prompt_defense.py` tests still passed (and one previously-failing case
now passes). The biggest mindset shift was accepting the "no new failures"
bar instead of "everything is green" — on someone else's code you own your
diff, not the whole repo, and you document the rest rather than trying to fix
the world in one PR.

**How did AI tools help — and where did they fall short?**
AI was most useful for breadth and boilerplate: brainstorming injection
attack categories (role-switching, instruction-override, template injection,
code execution, separator attacks) so my Tier 3 corpus was realistic rather
than a handful of obvious cases, drafting the parametrized pytest structure,
and getting the `(?:^|\n)` + `re.MULTILINE` anchoring right without a dozen
trial-and-error runs. It was a strong pair for "I know the shape I want, help
me fill it in fast."

Where it fell short was exactly the judgment calls that made this a Tier 3
issue. AI couldn't tell me the *maintainer's* intent on whether hardening was
in scope, couldn't decide that a pre-existing broken baseline meant I should
work to "no new failures," and couldn't feel the risk that anchoring "System:"
to start-of-string might start flagging a résumé line beginning with
"Override." Those needed me to read the actual repo state, weigh trade-offs,
and own a decision. AI accelerated the *how*; the *whether* and *why* stayed
mine.

**What would you do differently if you started over?**
I'd resolve the scope question earlier and in the open. I discovered the
newline bypass in Week 8 but carried the "suite only vs. suite + hardening"
question as an open blocker for too long; I should have posted it to the issue
thread or Slack the day I found it, so a maintainer could weigh in before I
committed to hardening. I'd also snapshot the failing baseline formally on day
one — a saved `make test-unit` / `make check` log — rather than reconstructing
the before/after later. And I'd open the PR as a draft sooner to give the
review request more runway; opening late is part of why no feedback landed
before the deadline.

**What are you most proud of from this module?**
That I turned a fuzzy assurance ("we think the safety layer works") into
per-commit evidence *and* found and closed a real security bug along the way.
The suite doesn't just pass today — it will fail loudly the moment a known
attack stops being blocked or a benign input starts being blocked, so the
defense can't silently regress. Finding the first-line bypass wasn't in the
issue description; it fell out of taking the reproduction step seriously, and
catching a genuine gap in production security code — not just adding tests
around existing behavior — is the thing I'm proudest of.
