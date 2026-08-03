# Journal — Issue #153

## Issue Selected

**Issue #153:** Faithfulness checker crashes when a context chunk has `text: None`
**Link:** https://github.com/ascherj/pathreview/issues/153
**Tier:** 1 (Starter — good for first-time contributors)

## Why This Issue Fits Me

I'm new to navigating a codebase this large, so I deliberately looked for a Tier 1 issue rather than a Tier 2 or 3 one — there's no extra credit for picking something harder, and I wanted my first contribution to be something I could fully understand end-to-end rather than something I'd have to partially guess at.

This issue fit that goal well: the bug report already identified the exact root cause (a `.get()` default-value gotcha) and gave exact reproduction steps and a named failing test. That meant I could focus my effort on verifying and understanding the fix deeply, rather than spending most of my time just locating the problem. It's scoped to a single function in a single file (`rag/evaluator/faithfulness_checker.py`), which matched the "single file/config" description of Tier 1 issues.

## "Is This Right For Me?" Checklist Reasoning

**Understanding the issue:** I can explain this without re-reading it: `dict.get(key, default)` only applies the default when the key is missing, not when it's present with value `None`. Before the fix, passing a context chunk like `{"text": None}` crashes the whole faithfulness check with a `TypeError`. After the fix, the same input degrades gracefully and returns a valid float score instead.

**Tier fit:** This is my first open source contribution, so Tier 1 was the right call rather than reaching for Tier 2 or 3 to "challenge myself." The issue lives entirely in one function in one file, matching the Tier 1 description exactly.

**Codebase readiness:** I located and read the exact function (`FaithfulnessChecker.check()`), not just the file, and could reason through the fix (`chunk.get("text") or ""`) before writing any code. I also read the full test file (`tests/unit/test_faithfulness_checker.py`) end-to-end, including the specific failing test (`test_none_context_chunk_text`) referenced in the issue.

**Scope and time:** The issue had 41 existing comments, but claims are non-exclusive and my grade comes from my own artifacts, so I didn't let that discourage me from picking it. I estimated this at the lower end of the 3–6 hour Tier 1 range for the core fix itself, though my actual time this week was higher due to unrelated local environment setup issues (BIOS/virtualization and two Docker service bugs), which I've documented separately. No blockers or dependencies were noted on the issue.

## Problem Summary

`FaithfulnessChecker.check()` crashes with a `TypeError` when a context chunk's `text` key is explicitly set to `None`, rather than missing entirely.

The bug is in this line:

```python
context_text = " ".join([
    chunk.get("text", "") for chunk in context_chunks
])
```

`dict.get(key, default)` only returns `default` when `key` is **absent** from the dictionary. If `key` exists but its value is `None`, `.get()` returns `None` — the default is never applied. When `context_chunks` contains a chunk like `{"text": None}`, this line collects `None` into the list being joined, and `" ".join([...])` raises:

TypeError: sequence item 0: expected str instance, NoneType found


This matches the reproduction steps in the issue exactly.

## Why This Matters

This is a realistic failure mode, not just a contrived edge case: a chunk with `text: None` could easily come from an upstream ingestion or retrieval step that returns a chunk record without content (e.g. a failed extraction, a placeholder, or a null field in a database row). The faithfulness checker should degrade gracefully in that case, not crash the whole review pipeline.

## Scope

- **File affected:** `rag/evaluator/faithfulness_checker.py`
- **Function affected:** `FaithfulnessChecker.check()`, specifically the `context_text` concatenation step
- **Tier:** 1 (single-file, single-line logic fix)
- **Existing test:** `test_none_context_chunk_text` in `tests/unit/test_faithfulness_checker.py` — already written, was failing before the fix, passes after

## Fix

Changed:

```python
chunk.get("text", "")
```

to:

```python
chunk.get("text") or ""
```

`chunk.get("text")` returns `None` whether the key is missing or explicitly `None`. `None or ""` normalizes both cases to an empty string, so the `join()` call always receives strings.

## Verification

Ran the full test file before and after the fix using `git stash` / `git stash pop` to isolate the effect of the change:

**Without the fix (stashed):**
- `test_none_context_chunk_text` → **FAILED** with the exact `TypeError` described in the issue
- 3 other tests failed for unrelated reasons (see below)

**With the fix (applied):**
- `test_none_context_chunk_text` → **PASSED**
- `test_missing_text_key_in_chunk` (a related but different case — missing key entirely) → **PASSED**, confirming no regression on the pre-existing "missing key" handling
- Same 3 unrelated tests still failed, identically, in both runs

## Out-of-Scope Findings

While testing, I found 3 pre-existing test failures unrelated to this issue:

- `test_partial_support_returns_middle_score`
- `test_multiple_context_chunks`
- `test_multiple_claims_varying_support`

All three fail because `_is_supported()` returns `False` even when there's clear keyword overlap between claim and context — this points to a bug in the stop-word filtering or the "≥2 meaningful tokens" threshold, not in anything touched by my fix. I confirmed this by stashing my change and re-running the tests: all 3 failed identically with and without my fix, proving they're independent of the `None`-handling bug in #153.

I'm leaving these out of this PR since they're outside the scope of #153 and would need their own investigation into the scoring/overlap logic.

## Branch / Commit

- Branch: `fix/153-faithfulness-none-context-text`
- Commit: `df03eb8` — `fix(rag): handle None context chunk text in faithfulness checker`

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/VanStacked/pathreview/commit/4757b4e

**Reproduction summary:** I wrote a small script (`reproduce_issue_153.py`) that calls `FaithfulnessChecker().check()` with a context chunk of `{"text": None}`. Running it confirmed the exact `TypeError: sequence item 0: expected str instance, NoneType found` described in the issue, proving the bug is real and reproducible in my local environment.

**PLAN.md link:** https://github.com/VanStacked/pathreview/blob/fix/153-faithfulness-none-context-text/PLAN.md

**Walkthrough video (recommended):** Not recorded.

**Blockers or open questions:** None significant. One open question I noted in PLAN.md's Risks section: whether `None` text values showing up in context chunks might point to a separate upstream ingestion bug worth investigating later — but that's out of scope for this fix.


## Week 9 — Solution building & PR submission

### Check-in 1

**Current progress:** All 5 sub-tasks from PLAN.md are complete: reproduced the bug, identified root cause, applied the fix (`chunk.get("text") or ""`), confirmed the target test passes, and isolated the fix's effect via `git stash`/`stash pop` against both my own branch history and against `main` directly.

**Next steps:** Run `make check` and `make test-unit` for a final pre-PR review, open the pull request with the full template filled in, and post it in Slack for peer/mentor feedback.

**Blockers:** None. Confirmed via direct comparison against `main` (53 failed/375 passed on `main` vs. 52 failed/376 passed on my branch) that my change introduces zero new failures and fixes exactly the one test tied to issue #153.

### Check-in 2

**PR link:** https://github.com/ascherj/pathreview/pull/294

**Branch:** `fix/153-faithfulness-none-context-text`

**What you built:** Fixed a crash in `FaithfulnessChecker.check()` where a context chunk with `text: None` caused a `TypeError`. The fix changes `chunk.get("text", "")` to `chunk.get("text") or ""`, so both a missing `text` key and an explicit `None` value are treated as empty string input instead of crashing.

**Tests added or updated:** No new test file was needed — `tests/unit/test_faithfulness_checker.py` already contained `test_none_context_chunk_text`, which was failing before this fix and passes after. I also verified `test_missing_text_key_in_chunk` (the related "key missing entirely" case) continues to pass with no regression. Added `reproduce_issue_153.py` at the repo root as a standalone reproduction script, separate from the test suite.

**Self-review confirmation:** [x] `make check` passes  [x] `make test-unit` passes

Note on `make test-unit`: 52 tests fail on this branch, all pre-existing and unrelated to my change. I confirmed this by comparing directly against `main`, which has 53 failures — one more than my branch, because this fix resolves exactly one of them (`test_none_context_chunk_text`). The remaining 52 are identical on both `main` and this branch, across modules I never touched (bias_detector, pii_scrubber, review_service, resume_parser, skill_extractor, tech_detector, and 3 unrelated tests within `test_faithfulness_checker.py` itself, isolated via `git stash` in my Week 7 entry above). My change introduces zero new failures.

**Draft PR feedback received from:** None — I'm working a week ahead of my cohort's schedule, so the Slack peer-review channel isn't active yet. I posted the PR link anyway in case anyone is available to look early.


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:** No feedback has come in on PR #294. I checked the PR's Conversation and Files Changed tabs after two weeks — zero comments, zero reviews. I opened my PR while working roughly a week ahead of my cohort's typical pace, so the Slack peer-review channel wasn't yet active, and no maintainer or peer engaged with it in the time since.

**How you responded:** N/A — no feedback received to respond to.

---

### Reflection

**What was harder than you expected?**
Environment setup, by a wide margin. I expected the actual code fix to be the hard part, but I spent significantly more time than anticipated on local environment issues that had nothing to do with the codebase itself: enabling virtualization in BIOS, installing WSL from scratch, and then debugging two separate Docker service failures (a NumPy 2.0/hnswlib incompatibility crashing ChromaDB, followed by a missing `curl` binary breaking its healthcheck). None of this was flagged as a likely blocker going in, and it ate up more time than the actual bug fix, test verification, and documentation combined.

**What did you learn about working in a large codebase?**
The biggest shift was learning to trust — and verify — existing conventions rather than only reasoning from first principles. When my `docker-compose.yml` fix or my `faithfulness_checker.py` change got auto-reformatted by `black`/`ruff` pre-commit hooks, I had to check the diff carefully to confirm nothing beyond formatting had changed, rather than assuming my mental model of "what I wrote" matched "what got committed." I also learned that a bug fix in a shared codebase isn't just about making the immediate test pass — I had to actively check whether my change affected anything else (the 3 pre-existing failing tests in the same file, and later the 52 pre-existing failures across the whole test suite), and prove that isolation rather than just assuming it.

**How did AI tools help — and where did they fall short?**
AI assistance was most valuable for two things: diagnosing unfamiliar error messages quickly (the ChromaDB/numpy traceback, the Docker Compose `command:` string-vs-list gotcha) and for structuring documentation (JOURNAL.md, PLAN.md, the PR description) in a way that matched what the rubric was actually asking for. Where it fell short was in situations that required me to actually run something and observe the real result — confirming the pre-existing test failures were identical on `main` versus my branch required me to actually execute `git checkout main` and `make test-unit` myself and report back the real output; no amount of reasoning about the code could substitute for that empirical check.

**What would you do differently if you started over?**
I'd verify my local dev environment (virtualization, Docker) *before* even starting to browse issues, rather than discovering the problems mid-setup. I'd also open my PR as a draft earlier in the process, right after my initial fix passed its target test, rather than waiting until PLAN.md and JOURNAL.md were both fully polished — that would have given any potential reviewer more lead time to engage, even though in my case the timing (working ahead of the cohort) meant no reviewer was likely available regardless.

**What are you most proud of from this module?**
Not the fix itself — it's the `git stash` verification process I built for isolating my change's effect. Rather than just trusting that my one-line fix "probably" didn't break anything else, I proved it two separate ways: once by stashing my own commit and rerunning the affected test file, and again by directly comparing `main`'s full test suite against my branch's. That gave me a PR description I could defend with actual evidence rather than assumptions, which felt like a genuinely professional habit rather than just finishing an assignment.