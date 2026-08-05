## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This bug is about the AI reviewer "remembering" things it shouldn't. When a user asks for a review, the system saves the results from the tools it ran and links them to that user's ID so it can reuse them later. The problem is that this saved information never gets cleared out. So if a user updates their portfolio and asks for a second review, the system just reuses its old saved results instead of actually re-checking the new version of their portfolio. That means the user could get feedback about problems they already fixed, because the AI never really looked again. The fix needs to happen in agent/memory/session_store.py, the file responsible for storing this session information, by making sure it clears out old data before starting a new review.

**Selection notes:** I chose this as a Tier 1 issue since it's my first time contributing to a large codebase, and a single-file, well-scoped bug felt like the right level of difficulty to start with. Before committing, I checked the issue comments and the cohort ledger — a couple of other students had also expressed interest in this issue, but the assignment clarified that claims are non-exclusive, so I was comfortable moving forward. The estimated 3–4 hours fits well within my available time before the Week 9 deadline given my other coursework, and there were no blockers or dependencies noted on the issue.

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/rehanNY06/pathreview-RB/commit/302e4de

**Reproduction summary:**
I wrote a standalone script that creates an Orchestrator with a fake tool that counts how many times it actually runs, then calls `.run()` twice for the same profile. The logs confirmed a "tool_result_cache_hit" on the second call, and the tool only executed once across both calls — proving the second review silently reused the first review's cached result instead of running fresh.

**PLAN.md link:** https://github.com/rehanNY06/pathreview-RB/blob/fix/43-agent-session-state-not-cleared/PLAN.md

**Walkthrough video (recommended):** (skipped, optional)

**Blockers or open questions:**
The real orchestration logic isn't wired into the live API yet — `_run_agent_orchestration()` in `review_service.py` is currently a placeholder that returns hardcoded data. I reproduced the bug directly against the `Orchestrator` class instead. I'm not yet sure if wiring the real orchestrator into the API is in scope for my fix, or a separate issue — planning to ask in Slack/office hours.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I implemented the core fix for issue #43: `Orchestrator` was creating a single `ContextManager` in `__init__`, which lived for the entire lifetime of the Orchestrator instance and let cached tool results leak across separate review requests. I changed it so a fresh `ContextManager` is created at the start of every `run()` call instead, guaranteeing no tool result can survive from one review into the next. This covers sub-tasks 1-3 from my PLAN.md.

**Next steps:**
I wrote unit tests (`tests/unit/test_orchestrator.py`) covering the fix, confirmed `make test-unit` shows no new failures compared to before my change, and confirmed `make check` is clean on my two files. Still need to open a draft PR for peer/mentor feedback and write the final PR description documenting the pre-existing, unrelated test/lint failures I found in the codebase.

**Blockers:**
None blocking right now. One open question I still want feedback on: whether wiring the real `Orchestrator` into the live API (`review_service.py` currently uses a placeholder) is in scope for this issue, or a separate concern -- I reproduced and fixed the bug directly against the `Orchestrator` class itself.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/663

**Branch:** fix/43-agent-session-state-not-cleared

**What you built:**
Fixed issue #43 by changing `Orchestrator` to create a fresh `ContextManager` at the start of every `run()` call instead of storing one on `self` for the whole lifetime of the orchestrator. This preserves memoization within a single review while guaranteeing tool results can never leak into a later, separate review request.

**Tests added or updated:**
Added `tests/unit/test_orchestrator.py` with 5 tests: re-execution across separate reviews for the same profile, no cache sharing between different profiles, intra-review memoization still working, `run()`'s return shape, and graceful handling of an unknown tool in the plan.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Both commands were run and confirmed to introduce zero new failures compared to the pre-fix code -- the pre-existing failures/errors in unrelated files are documented in my PR description.)

**Draft PR feedback received from:** none (posted in Slack, but no responses came in before the deadline)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review
(Note: reviewer feedback is not a feature in Summer 2026, per course announcement.)

**Summary of feedback:**
No review came in on PR #663 by the end of the module. I posted the draft PR in Slack asking for early feedback, but no one responded before the deadline.

**How you responded:**
N/A -- no feedback was received to respond to.

---

### Reflection

**What was harder than you expected?**
Getting my local environment running reliably was a bigger time sink than the actual bug fix. I hit a Docker container (`vector-db` / ChromaDB) that crashed on every startup due to a `numpy` version incompatibility baked into the image itself -- nothing I could fix by restarting or rebuilding, since the issue was internal to the pinned image version. I also kept running commands in PowerShell instead of Git Bash out of habit, which broke `make` repeatedly until I got in the habit of checking which shell I was in. Tracing the actual bug was harder than I expected too -- the issue title pointed at `session_store.py`, but that file turned out to be completely correct on its own. The real bug was two layers away, in how `Orchestrator` instantiated `ContextManager` in `__init__` instead of scoping it to a single `run()` call. I had to read through `orchestrator.py`, `context_manager.py`, and trace the call chain from `main.py` through `reviews.py` through `review_service.py` before I found where the actual orchestration logic lived (and even then, found out it was just a placeholder that isn't wired into the live API yet).

**What did you learn about working in a large codebase?**
The bug wasn't where the issue title said it would be. That was the biggest lesson -- issue titles and docstrings point you in a direction, but the actual root cause can be one or two layers removed from where you start looking. I also learned that a codebase can have pre-existing, unrelated failures (53 failing tests, 179 lint/type errors) that have nothing to do with what you're working on, and that's normal -- the standard isn't "leave the codebase perfect," it's "don't make it worse." Documenting that clearly in a PR description, backed by a before/after comparison (I used `git stash` to prove the same 53 failures existed before and after my change), felt like a more honest and useful contribution than silently ignoring them or trying to fix everything at once.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for reading and tracing code I didn't write -- following the chain from the API route through the service layer to the actual orchestrator, and spotting that `ContextManager`'s own docstring ("within-session memoization") directly contradicted how it was being used (stored for the lifetime of the Orchestrator instance). It was also useful for quickly explaining unfamiliar tooling errors (Docker Compose output, pre-commit hook failures, mypy error messages) in plain language when I didn't recognize them. Where it fell short: it couldn't actually run commands on my machine, so every fix still required me to manually copy files, run terminal commands, and report back results -- which meant a lot of back-and-forth for things that would have been one step if I'd had direct file access. It also couldn't diagnose the Docker/numpy issue with certainty since it couldn't execute anything inside the container itself; we could only reason about it from the log output.

**What would you do differently if you started over?**
I'd read the full call chain (API route -> service -> orchestrator -> memory) before writing any reproduction code, instead of starting with the file the issue title pointed at. I'd also set up my environment more carefully at the start -- confirming Git Bash vs PowerShell early, and checking `docker compose ps -a` (not just `ps`) from the very first setup so I'd have caught the vector-db crash sooner instead of discovering it mid-restart.

**What are you most proud of from this module?**
Proving the bug was real before writing any fix. Instead of guessing at the cause and patching something, I wrote a standalone script with a fake tool that counted its own executions, which gave me clear, undeniable log output (`tool_result_cache_hit`) showing the exact mechanism of the bug. That same script became the basis for my actual regression test, so the proof-of-bug and the safety-net-against-regression were the same piece of work.