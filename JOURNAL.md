# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/codepath-ai201/pathreview/issues/64

**Issue title:** Prompt injection defense doesn't sanitize newline characters in user-supplied resume text

**Tier:** [ ] Tier 1 [x] Tier 2 [ ] Tier 3

**Problem summary:**
PathReview's prompt-injection defense in `safety/prompt_defense.py` sanitizes
resume text before it is inserted into the LLM system prompt, but it only strips
the characters `<`, `>`, and `{`. Because it never handles newline-based
sequences, an adversarial user can embed patterns like `\n---\n` or `\nSystem:`
in their resume to visually terminate the system prompt and inject their own
instructions, hijacking the agent's behavior. The current sanitizer therefore
gives a false sense of safety while leaving the most practical injection vector
open. A successful fix would detect and neutralize these newline/delimiter and
role-label patterns (in addition to the existing character filtering) so that
attacker-controlled resume text can no longer break out of its intended context,
backed by unit tests covering the `\n---\n` and `\nSystem:` cases.

**Branch name:** fix/64-prompt-injection-newline-sanitizer

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/edombelayneh/pathreview/commit/31978e4436f2eca89bd6a4c19bfa81b7e9b8ba58

**Reproduction summary:**
Ran user-supplied resume strings containing `\nSystem:` and `\n---\n` through
`PromptDefense.sanitize()` and observed the output was byte-for-byte identical to
the malicious input — so `is_injection_attempt(sanitize(x))` still returns `True`.
Captured this as two failing unit tests (`TestNewlineSanitizationRepro` in
`tests/unit/test_prompt_defense.py`) that assert the expected post-fix behavior.

**PLAN.md link:** https://github.com/edombelayneh/pathreview/blob/fix/64-prompt-injection-newline-sanitizer/PLAN.md

**Blockers or open questions:**
While reproducing, I found a _second_, pre-existing gap: `is_injection_attempt()`
misses role labels with a space before the colon (e.g. `"System :"`), so the
existing `test_whitespace_variations_detected` test already fails independent of
my change. Open question for Week 9: fix that in the same PR or scope it out.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All implementation sub-tasks from PLAN.md are done. I extended
`PromptDefense.sanitize()` in `safety/prompt_defense.py` to (1) normalize newline
variants (`\r\n`, `\r`, U+2028, U+2029) to `\n`, then (2) neutralize the
newline-anchored injection sequences the detector already flags — separator lines
(`\n---\n`), role labels (`\nSystem:`/`Human:`/`Assistant:`), and override lines
(`\nIgnore`/`Forget`/`Disregard`/`Override`). The two reproduction tests from
Week 8 now pass, and I added `TestNewlineSanitizationFix` (9 tests) covering
CRLF/CR, Unicode separators, case-insensitivity, stacked injections, idempotency,
and a false-positive guard so a normal multi-paragraph resume stays readable and
un-flagged. Scoped `ruff`/`black`/`mypy` are clean on both changed files, and
`pytest tests/unit/test_prompt_defense.py` is 42 passed / 1 failed (only the
pre-existing, unrelated `test_whitespace_variations_detected`). Draft PR is open.

**Next steps:**
Post the draft PR in the cohort Slack channel for peer review, address any
feedback, then mark the PR "Ready for review." Finalize Check-in 2 and submit the
branch URL via the course portal.

**Blockers:**
Resolved the Week 8 open question: the pre-existing `test_whitespace_variations_detected`
failure is a separate bug in `is_injection_attempt()` (not `sanitize()`), so I
scoped it out of this PR and documented it in the PR's "Notes for Reviewers"
rather than expanding scope. No active blockers.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/602

**Branch:** `fix/64-prompt-injection-newline-sanitizer`

**What you built:**
Extended `PromptDefense.sanitize()` to neutralize newline-based prompt-injection
sequences (separator lines, role labels, override lines) after normalizing newline
variants, so `is_injection_attempt(sanitize(x))` is `False` for attacker-controlled
resume text. The change is surgical (legitimate multi-paragraph resumes survive
intact) and idempotent, and the sanitizer patterns mirror the detector's to prevent
the two from drifting apart again.

**Tests added or updated:**
`tests/unit/test_prompt_defense.py` — the two Week 8 reproduction tests
(`TestNewlineSanitizationRepro`) now pass as regression tests, plus a new
`TestNewlineSanitizationFix` class (9 tests) covering CRLF/bare-CR, Unicode line
separators, case-insensitive role labels, override lines, stacked injections,
idempotency, empty/whitespace safety, and a legitimate-resume false-positive guard.

**Self-review confirmation:** [x] make check passes [x] make test-unit passes
_(In this codebase there are documented pre-existing failures on the base commit —
repo-wide `make check` reports 182 ruff / 52 black / 5 mypy issues and `make
test-unit` reports 55 pre-existing failures. "Passes" here means my change
introduces **no new** failures; scoped to my two files, ruff/black/mypy are clean
and the only failing test is the pre-existing `test_whitespace_variations_detected`.
See the PR's "Notes for Reviewers.")_

**Draft PR feedback received from:** none — posted the draft PR in the cohort
Slack channel requesting peer review, but received no feedback before the
submission deadline. Marked the PR "Ready for review" and self-reviewed against
`docs/CONTRIBUTING.md` (branch naming, Conventional Commits, docstrings, and the
scoped `ruff`/`black`/`mypy`/test checks documented above).

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes [x] No — still awaiting review

**Summary of feedback:**
No feedback arrived. I re-checked [PR #602](https://github.com/ascherj/pathreview/pull/602)
during Week 10 and there were no review comments, line comments, or requested
changes from maintainers, and no replies to the peer-review request I posted in
the cohort Slack channel in Week 9.

**How you responded:**
No changes were warranted, so I made none — the branch is unchanged since the
Week 9 submission commit. Since I had no external reviewer, I ran a
second self-review pass instead of leaving the time unused: re-read the diff on
`safety/prompt_defense.py` cold, re-confirmed `sanitize()` still has no callers
outside the module and its tests, and re-ran the scoped checks. Results, stated
against BASELINE.md: `black` clean and `mypy` clean on both changed
files; `ruff` reports 1 error, the pre-existing `F841` unused-variable at
[tests/unit/test_prompt_defense.py:245](tests/unit/test_prompt_defense.py#L245)
that was in the baseline and is not mine (my change actually _removed_ the
baseline's `I001` error in `safety/prompt_defense.py`); `pytest
tests/unit/test_prompt_defense.py` = 42 passed / 1 failed, that one being the
pre-existing `test_whitespace_variations_detected` detector bug I deliberately
scoped out and documented in "Notes for Reviewers." Net against baseline: one
lint error fixed, no new failures. Nothing new surfaced, so I left the PR as-is
rather than churning commits for their own sake.

---

### Reflection

**What was harder than you expected?**
Honestly, the hardest part had nothing to do with the bug. It was figuring out
what "passing" was supposed to mean here. CLAUDE.md says code has to pass
`make check && make test-unit` before a PR, and when I ran those on a clean
checkout I got 182 ruff errors, 52 files black wanted to reformat, 5 mypy errors,
and 55 failing tests. I spent an embarrassing amount of Week 8 assuming I'd broken
something. I hadn't — it was all already like that.

That's what made me write BASELINE.md, which at the time felt like procrastinating
on the real work. It's just a snapshot of the failures at commit `e834117`, scoped
down to the two files I was going to touch. It ended up being the thing I leaned on
most. Without it I had no way to say "these failures aren't mine" and actually mean
it.

The other thing that surprised me was how easy it is to over-fix. The regexes look
like a five-minute job until you sit down and write the test for a normal resume.
Real resumes have blank lines, Markdown `---` rules, and lines like "Systems
Engineer" or "System Design: distributed queues." A greedy pattern that kills every
`---` and every "System" passes all the security tests and quietly wrecks people's
resumes, and nothing tells you. I also got bitten by ordering: my first
`_SEPARATOR_RE` ate the newline that `_ROLE_LABEL_RE` needed, so `"\n---\nSystem:"`
only got half-defused. Adding the `(?=\n|$)` lookahead fixed it, but I only found
it because I'd written a stacked-injection test. If I hadn't, it would have shipped.

**What did you learn about working in a large codebase?**
The fix is about 15 lines. Almost all of my time went to everything around it —
grepping for callers of `sanitize()` to make sure nobody depended on newlines
surviving, checking `safety/content_filter.py` for duplicate sanitizing logic,
and going back and forth on whether the neighboring bug belonged in my PR.

While reproducing I found that
`is_injection_attempt()` misses `"System :"` (space before the colon), which is why
`test_whitespace_variations_detected` was already red. It's basically a
one-character regex change and I really wanted to just fix it. In my own project I
would have. But it's a different method with a different failure
mode, it changes detection behavior I don't fully understand the downstream of, and
it makes my diff bigger. So I
left it and wrote it up in "Notes for Reviewers" instead. It's a decision I
didn't know was a decision before this module.

The other thing I noticed: this bug wasn't really a coding mistake. Two methods in
the same file disagreed. `is_injection_attempt()` already knew `\nSystem:` was
dangerous, and `sanitize()` just never got updated to match. Nobody did anything
wrong, they drifted. That's why I wrote my patterns to mirror the detector's and
said so in a comment — otherwise the same thing happens again in a year.

**How did AI tools help — and where did they fall short?**
It was good at getting me oriented fast: finding `sanitize()`, tracing
who called it, and listing newline variants I wouldn't have thought of. It was also useful for the tedious stuff, docstrings,
matching the file's comment style, drafting a first pass at the edge-case list.

Where it fell short was judgment. Two things stood out. First, when I mentioned the
`"System :"` detector bug, the immediate suggestion was to fix it. It never
occurred to the tool that a bigger diff costs a reviewer something, because it has
no idea who's reviewing.  
Second, it told me the regexes worked before the
stacked-injection test existed, they passed every test that existed at that moment. That's the pattern I'd flag to anyone: AI is very good at
writing code that passes the tests you thought of, and gives you no warning at all
about the ones you didn't.

**What would you do differently if you started over?**
Take the baseline before touching anything. I wrote BASELINE.md partway through
Week 8, after already losing time to "wait, did I break this?" Ten minutes up front
would have saved all of that, and it's the first thing I'd do in any repo I don't
know now.

I'd also ask for review way earlier. I dropped the draft PR in Slack basically at
the Week 9 deadline, which gave nobody a real chance to look at it.

**What are you most proud of from this module?**
The false-positive test — the one that just runs a normal multi-paragraph resume
through `sanitize()` and checks it comes out readable and unflagged. It's the least
impressive line in the diff. But it's the only test in there that's on the user's
side instead of the attacker's, and writing it is what forced me to actually think
about the cost of the fix. Stopping every injection is easy if you're allowed to
destroy the input; all the security tests still go green.
