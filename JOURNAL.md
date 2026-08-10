## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user #43

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue stems from how `agent/orchestrator.py` interacts with the `SessionStore` in `agent/memory/session_store.py`. Specifically, the orchestrator's `run` method passes the user's `profile_id` as the cache key when storing and retrieving session state, rather than generating a unique identifier for each distinct review request. As a result, when a user requests a subsequent review, the orchestrator fetches stale tool results from their previous session instead of performing a new analysis. A successful fix will update the orchestrator to either clear the session state between requests or use a uniquely generated session ID, ensuring the agent always evaluates the user's most recent portfolio updates.

**Scope fit:**
I selected this issue because it aligns well with my current comfort level in Python, focusing on state management within a specific component rather than requiring sprawling architectural changes. Since I have 3-6 hours available for a Tier 1 issue, addressing the orchestrator's session logic is a realistic and appropriately scoped challenge.

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/bbdevelops/pathreview/commit/c87b97f95f7421d3f614d1accbeac4cbf3ea5f16

**Reproduction summary:**
Ran `scripts/reproduce_issue_43.py`, which drives `Orchestrator.run()` twice for the same `profile_id` (README-only, then resume-only) against an in-memory fake Redis. After run 2, the persisted session state still contained `readme_scorer` from run 1 — confirming stale state leaks across reviews because `run()` merges new results onto prior state (`agent/orchestrator.py:66`) and re-keys on `profile_id`. Further code review found a second stale-data path: the in-memory `ContextManager` is instantiated once per Orchestrator (`:29`) rather than per review, so `cached_results` accumulates and `market_analyzer`'s constant input serves the prior run's result.

**PLAN.md link:** https://github.com/bbdevelops/pathreview/blob/fix/43-agent-session-state-not-cleared/PLAN.md

**Blockers or open questions:**
The fix must clear **both** cache layers — the Redis `SessionStore` and the in-memory `ContextManager` (`orchestrator.py:29`/`:75`, with `market_analyzer` at `:130`); a Redis-only fix is partial. Also confirm whether wiring `Orchestrator` into the production review pipeline (`core/services/review_service.py::_run_agent_orchestration` is currently a placeholder) is in scope for #43 — assuming not; the fix is verified via the repro script and a new unit test.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All five PLAN.md sub-tasks are implemented, verified, and committed on
`fix/43-agent-session-state-not-cleared`:

- **Sub-task 1 — SessionStore (Layer 1):** `Orchestrator.run()` no longer loads and
  merges the prior review's state; it now clears the key and persists only the current
  run's results (`delete()` + `set()`). Commit `6f98d8c` (`fix(agent)`). The pre-commit
  hooks reformatted the previously non-compliant `orchestrator.py`, so that ruff/black
  churn was isolated in a separate `style(agent)` commit `127f8ca` to keep the fix diff
  minimal (~6 lines).
- **Sub-task 2 — ContextManager (Layer 2):** `run()` recreates `self.context_manager`
  each review, fixing both the `cached_results` accumulation and the `market_analyzer`
  constant-input stale cache hit. Commit `977483b` (`fix(agent)`).
- **Sub-task 3 — Regression test:** new `tests/unit/test_orchestrator.py` (4 tests)
  covering both layers on one reused Orchestrator. Per the Week 8 feedback, the
  `market_analyzer` check asserts re-execution by a Mock spy's **call count** (== 2),
  not by output (its constant input makes cached and fresh output identical). Commit
  `6f1d2f8` (`test(agent)`). Verified it fails 3-of-4 against pre-fix code and passes
  against the fix.
- **Sub-task 4 — SessionStore unit test:** new `tests/unit/test_session_store.py`
  (12 tests) — get/set/delete round-trip, `delete()` removes the key, the
  `session:<id>` key + 3600s TTL contract, and log-and-swallow on Redis errors. Commit
  `11b24e1` (`test(agent)`).
- **Sub-task 5 — Reproduction script:** flipped `scripts/reproduce_issue_43.py` into a
  fix-verification harness (exit 0 = all layers clean, non-zero = regression). Commit
  `abd84ee` (`test(agent)`).

Verification: `python scripts/reproduce_issue_43.py` prints `[FIX VERIFIED]` and exits 0
(all three layers clean; `market_analyzer` executes 2x). `make test-unit` reports
53 failed / 391 passed — the 16 new #43 tests all pass and the 53 pre-existing failures
(in unrelated modules) are unchanged.

**Next steps:**
- Open a **draft PR** against `ascherj/pathreview` using the PR template (Summary, Issue
  `Closes #43`, Changes, Testing, Notes for Reviewers).
- Request peer/mentor review in the course Slack channel; address any feedback, then mark
  the PR ready for review.
- Fill in Check-in 2 (PR link, tests summary, both self-review boxes) and submit the
  branch `/tree/fix/43-agent-session-state-not-cleared` URL via the course portal.

**Blockers:**
None blocking. Noted for the PR: `make check` and `make test-unit` have **extensive
pre-existing failures unrelated to #43** — `ruff check .` ≈179 errors, `black .` would
reformat ≈52 files, `mypy` halts on missing third-party stubs (PyPDF2, jose, passlib,
rank_bm25) plus a numpy/Python-3.13 stub error, and 53 unit tests fail. My four changed
files are individually clean under ruff/black/mypy and introduce zero new failures, which
the PR will document per the course's "no new failures" standard.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/512

**Branch:** fix/43-agent-session-state-not-cleared

**What you built:**
`Orchestrator.run()` was leaking one review's state into the next for the same `profile_id`
across two independent caches, so a later review could reflect tool results from an earlier
submission. The fix clears both layers: it stops loading and merging the prior review's
persisted state and instead writes only the current run's results to the Redis `SessionStore`
(calling the previously-unused `delete()` before `set()`), and it recreates the in-memory
`ContextManager` at the top of every `run()` so memoized results — including `market_analyzer`'s
constant-input result — no longer carry over. Net effect: each review reflects only the current
submission across both layers.

**Tests added or updated:**
Two new unit test files, plus the reproduction script:
- **`tests/unit/test_orchestrator.py`** — 4 regression tests
  (`TestOrchestratorClearsStateBetweenReviews`) that run two consecutive reviews (README-only,
  then resume-only) on a single *reused* Orchestrator and assert no state leaks across either
  layer: run 2's persisted Redis payload holds only run 2's tools (no `readme_scorer`), run 2's
  `cached_results` doesn't carry run 1's memoized entries, and `market_analyzer` re-executes each
  review — asserted by Mock `call_count == 2`, because its constant input makes a cached result
  and a fresh result identical, so output alone can't distinguish them.
- **`tests/unit/test_session_store.py`** — 12 unit tests covering `SessionStore`'s get/set/delete
  round-trip, that `delete()` actually removes the key (the method the fix activates) and is a
  safe no-op on a missing key, that `set()` overwrites rather than merges, the `session:<id>` key
  prefix + 3600s default/custom TTL contract, and log-and-swallow behavior on Redis errors and
  invalid JSON.
- **`scripts/reproduce_issue_43.py`** — flipped from a bug-demonstration into a fix-verification
  harness (exit 0 = all layers clean, non-zero = regression).

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
*(Per the course rule for codebases with documented pre-existing failures, "passes" = my changes
introduce no new failures. The four changed files are individually clean under ruff/black/mypy;
`make test-unit` is unchanged at 53 pre-existing failures / 391 passed, with the 16 new #43 tests
passing. The pre-existing failures are documented in the PR and in Check-in 1.)*

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [] Yes  [X] No — still awaiting review

**Summary of feedback:**
No feedback.

**How you responded:**
N/A

---

### Reflection

**What was harder than you expected?**
Navigating the codebase was a bit of a challenge. I'm used to building something on my own or at very least designing the system architecture and using AI. Getting dropped into this codebase and having to orient myself was definitely a struggle.
Setting up tests was also a little difficult. It wasn't obvious at first what the best way to approach reproducing the issue and testing the solution.

**What did you learn about working in a large codebase?**
I learned that rushing in and trying to immediately diagnose an issue is probably not the best solution. Taking time to understand how the pieces of the codebase fit together helps alot with keeping track of problems down the road. I also learned that sometimes issues can have more than one cause and you need to be careful about not assuming you have fixed something by addressing one cause.

**How did AI tools help — and where did they fall short?**
It helped diagnose the initial layer of the bug, but failed (at least at first) to find another more subtle manifestation of the bug. Once it was made aware of the secondary layer of the error it was able to diagnose it and help address it, but on it's own it failed to see the second order issue. AI tools helped with developing a test script as my issue wasn't readily observed by running the existing test suite. 

**What would you do differently if you started over?**
If I were to do this again I'd likely take more notes as I was going through the code to be able to reference the connection points between files, classes, functions etc. I naively thought I'd be able to just build a mental model of the project and go from there, but that wasn't the best strategy. The issue selection was alright, though it was still a bit of a challenge despite being tier one. The solutions ended up being relatively simple, but I intentionally limited the scope to just addressing the issue as specified. It's likely that there was a bigger issue hidden behind mine that would have required a larger system archtitecture shift to address

**What are you most proud of from this module?**
Finishing it and surviving the course. More specifically, it was my first time going through this process of developing a PR for an issue, working on it and submitting it, so I'm proud of that. Or at very least I'm happy that I have seen what it's like and know some best practices for how to approach doing this kind of thing in the future. 

---

### Part 1 — Understanding the Issue

**Can I explain what this issue is asking for in my own words?**

Paraphrase the issue without looking at it. If you can't, you don't understand it well enough yet. Read the full issue body, look at any linked PRs or comments, and try again.

[X] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.

**Do I understand which part of the app is affected?**

Check the labels on the issue — they often indicate the area (api, rag, ingestion, frontend, etc.). Look at the referenced files if any are mentioned. Find those files in the repo.

[X] I've located the relevant files and confirmed they exist in the codebase.

**Do I understand what "done" looks like?**

Can you describe what the app should do (or not do) once the issue is fixed? If the issue has acceptance criteria, read them carefully. If it doesn't, try writing your own — that forces you to understand the scope.

[X] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

---

### Part 2 — Tier Fit

**Is the tier a realistic match for where I am right now?**

[X] If this is my first open source contribution: I'm choosing Tier 1.

[ ] If I've contributed to large codebases before: Tier 2 or 3 is fair game.

[ ] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.

---

### Part 3 — Codebase Readiness

**Can I find the relevant code?**

Before claiming the issue, locate the specific function, route, or module it describes. Don't rely on grep alone — open the file, read the surrounding context, and confirm you're in the right place.

[X] I've found and read the specific code the issue references (not just the file — the function or section).

**Do I understand the surrounding code well enough to change it safely?**

You don't need to understand the whole codebase. But you need to understand the file you're about to edit well enough to predict what a change will break. Read the function signatures, docstrings, and any callers.

[X] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.

**Have I read the relevant test file?**

Find the test file for the module your issue touches (tests/unit/ is the right place to start). Look at how existing tests are structured — fixtures, assertions, mock patterns. You'll need to write at least one new test.

[X] I've found the test file for my module and read at least one test end-to-end.

---

### Part 4 — Scope and Time

**How many others are already working on this issue?**

Claims are non-exclusive — more than one student may work on the same issue, and your grade comes from your own artifacts, never from being first. Still, check the issue comments and the Claims column in the Issue Catalog tab of the cohort ledger: a less-crowded issue of the same tier can mean smoother coaching and peer review.

[X] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.

**Is the scope realistic for Weeks 8–9?**

You have roughly two weeks to implement, test, and submit a PR. Tier 1 issues should take 3–6 hours of focused work. Tier 2 issues may take 8–12 hours. Tier 3 issues can take significantly longer.

Think about your week — other classes, work, other commitments. Is this achievable?

[X] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.

**Are there any blockers or dependencies?**

Some issues say "blocked by #X" or reference another issue that needs to be resolved first. Check the issue for any such dependencies.

[X] This issue has no open blockers or dependencies on other unresolved issues.
