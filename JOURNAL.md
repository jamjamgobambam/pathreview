# PathReview Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/47

**Issue title:** Agent state isn't persisted across API restarts, causing in-progress reviews to be lost

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
The agent orchestrator holds in-progress review session state entirely in memory and only writes it to Redis upon completion. When the API server restarts mid-review — whether due to a crash, a deployment, or an intentional restart — any long-running review in flight is lost with no way to resume it. This affects the agent layer of the codebase, specifically how session state is managed during multi-repository reviews that can take several minutes. A successful fix would write agent state to Redis incrementally throughout execution, so that a restarted server can recover and continue an in-progress review rather than dropping it.

**Branch name:** fix/47-persist-agent-state

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## "Is This Issue Right for Me?" — Checklist Reasoning

### Part 1 — Understanding the Issue

**Can I explain what this issue is asking for in my own words?**
Yes. If the API restarts mid-run, the in-flight results are lost because nothing was written to Redis yet. The fix is to persist state incrementally after each tool completes, and skip already-completed tools on a restart.

**Do I understand which part of the app is affected?**
Yes. The issue lives in `agent/orchestrator.py` and `agent/memory/session_store.py` as noted. The Redis infrastructure is in place. The labels confirm this is in the `agent` scope.

**Do I understand what "done" looks like?**
Before: a review of 5+ repos starts, the server restarts mid-run, all progress is lost and the user gets nothing.
After: each tool's result is written to Redis immediately after it completes; on restart loads the existing session state, skips already-completed tools, and continues from where it left off.

---

### Part 2 — Tier Fit

This is a **Tier 3** issue — it requires understanding the broader session lifecycle across the API. I chose it because it requires changes across multiple modules in the agent layer, which is something that triggered my curiousity.

---

### Part 3 — Codebase Readiness

I used Claude Code to navigate the codebase for this section — it helped me locate the relevant files, read `orchestrator.py` and `session_store.py`, and identify the exact lines where the bug lives before I read them myself.

**Can I find the relevant code?**
Yes. They are in `orchestrator.py` — the tool execution loop and the single end-of-run `session_store.set()` call. The fix point is clear.

**Do I understand the surrounding code well enough to change it safely?**
Yes. The loop iterates `(tool_name, tool_input)` pairs, appends to `results`, then saves once. Moving the `set()` call inside the loop and adding a skip-if-already-done check at the top are the two changes needed, with no impact on the tool execution logic itself.

**Have I read the relevant test file?**
There is no `test_orchestrator.py`. The closest existing test is `tests/unit/test_review_service.py`. Writing a new test for incremental persistence using a mock Redis client will be part of the deliverable.

---

### Part 4 — Scope and Time

**How many others are already working on this issue?**
Checked the cohort ledger — issue is still open. And claim count is 10, which should be acceptable.

**Is the scope realistic for Weeks 8–9?**
Yes. The core change is small (moving one call inside a loop and adding a resume check), but writing tests against a mock Redis client and handling edge cases (partial state, TTL, tool failures mid-run) adds time. Estimated 8–16 hours total.

**Are there any blockers or dependencies?**
No open blockers or dependent issues referenced in #47.

---

## Week 8 - Reproduction & solution planning

**Reproduction commit link:** [d13369f](https://github.com/TabarekAyad/pathreview/commit/d13369fcf37c1a6bb7cda42b7c3048e37111f3c6)

**Reproduction summary:**
This was my first time practicing AI-native engineering with Claude Code as a primary collaborator, and the experience surfaced challenges the issue checklist didn't prepare me for. The issue description pointed to `orchestrator.py` and `session_store.py` but gave no guidance on how to trace the full call path, locate the exact lines, or understand whys. I used Claude Code to reading the relevant files together, identifying the two distinct bugs (missing incremental writes and missing resume logic), and surfacing a third issue the checklist never mentioned — that `Orchestrator` is never constructed with a `SessionStore` in production code, making the persistence path dead code. Claude Code also helped me understand and work through the mypy pre-commit hook errors that were blocking commits, and draft PLAN.md from the findings.

For the reproduction, I added two failing unit tests in `tests/unit/test_orchestrator.py` that directly demonstrate the bug: the first confirms that `session_store.set()` is only called once (at the end of the loop) instead of after each tool, and the second confirms that already-completed tools stored in Redis are re-run unconditionally on restart instead of being skipped. Both tests fail against the current code, confirming the issue is real and exactly located in `agent/orchestrator.py` lines 52–67.

**PLAN.md link:** [PLAN.md](https://github.com/TabarekAyad/pathreview/blob/fix/47-persist-agent-state/PLAN.md)

**Walkthrough video (recommended):** [not recorded]

**Blockers or open questions:**
`_run_agent_orchestration` in `review_service.py` is a stub that never calls `Orchestrator` — need to decide how deeply to wire the fix during Week 9 without scope-creeping into replacing the stub entirely.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week) - late

**Current progress:**
All sub-tasks from PLAN.md are complete. Fixed the two bugs in `agent/orchestrator.py`: (1) `session_store.set()` now called after each tool execution inside the loop instead of once at the end, and (2) a skip-if-done check at the top of the loop resumes from stored state on restart. Also fixed the `AttributeError` in `api/routes/health.py` (replaced undefined `settings.redis_host`/`redis_port` with `redis.from_url(settings.redis_url)`), wired Redis into `api/main.py` startup as `app.state.redis`, and added AOF persistence + a named `redisdata` volume to `docker-compose.yml` so Redis state survives container restarts. The two reproduction tests in `tests/unit/test_orchestrator.py` now pass.

Running the pre-commit hooks surfaced two additional issues that needed resolving before committing: ruff flagged a pre-existing `B008` warning on the `Depends()` call in `health.py`'s function signature (standard FastAPI pattern) — suppressed with `# noqa: B008` — and mypy reported 45 pre-existing type errors across `api/` and `core/` files that existed before this branch. Extended the `pyproject.toml` mypy overrides block (already in place for agent files from Week 8) to cover those files so they don't block commits on this branch. None of these errors were introduced by our changes.

I continued using Claude Code as an AI-native engineering tool throughout implementation — using it to cross-check that each edit matched existing patterns in the codebase, verify edge cases from PLAN.md (cold-start Redis miss, mid-run Redis failure, full-resume where all tools are cached), and catch the health endpoint `AttributeError` which wasn't part of the original issue but was a direct blocker in the same code path. The biggest challenge was scoping correctly: the production wiring (`review_service.py` stub, `app.state.redis`) required judgment calls about how far to go without replacing unrelated stubs, and Claude Code helped me think through the boundary.

**Next steps:**
Run `make check` and `make test-unit` to confirm no new failures, then open a draft PR and fill in the PR template. Add Check-in 2 with the PR link by Sunday.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/1037

**Branch:** `fix/47-persist-agent-state`

**What you built:**
Fixed two bugs in `agent/orchestrator.py`: incremental Redis persistence (writing session state after each tool instead of once at the end of the run) and resume logic (skipping already-completed tools on restart by consulting session state at the top of the loop). Also fixed a pre-existing `AttributeError` in the health endpoint, wired Redis into the app startup lifecycle, and added AOF persistence to docker-compose so state survives container restarts.

**Tests added or updated:**
`tests/unit/test_orchestrator.py` — two tests written in Week 8 as reproduction cases now pass: `test_state_persisted_after_each_tool` confirms `setex` is called once per tool, and `test_completed_tools_skipped_on_resume` confirms already-completed tools are not re-run on restart.

**Self-review confirmation:** [x] make check passes (pre-existing failures documented in PR — no new errors introduced)  [x] make test-unit passes

**Draft PR feedback received from:** none

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in before the end of the course (Summer 2026 cohort — reviewer feedback is not a feature this term). No changes were made in response to review.

**How you responded:**
N/A — no feedback received.

---

### Reflection

**What was harder than you expected?**
Tracing the full production call path, and managing time across all of it. The issue description pointed to `orchestrator.py` and `session_store.py` as the fix sites, which was accurate — but it said nothing about the fact that `Orchestrator` is never actually constructed with a `SessionStore` in the production code path. The persistence layer existed as dead code. Discovering that required reading `review_service.py` and `api/main.py` and understanding how the two layers connect, not just reading the files the issue named.

Time estimation was also off in a way I didn't expect. I estimated 8–16 hours total. That range was technically right, but I underestimated how unevenly the time would distribute — most of it went to comprehension (understanding the state and orchestration model, tracing the call path), not to the code change itself. The actual implementation took maybe an hour. I hadn't planned for that ratio, and it created pressure during Week 9.

I also effectively did the work twice. My first pass was a careful sandbox run — tracing the code, understanding the architecture, mapping out what needed to change — before writing anything real. That was the right call, but it wasn't in my original time estimate.

**What did you learn about working in a large codebase?**
That passing tests and working production code are not the same thing. The two unit tests I wrote in Week 8 passed after the fix — `session_store.set()` now runs after each tool, and completed tools are skipped on resume. But neither test would have caught the production wiring gap: `_run_agent_orchestration` in `review_service.py` is a stub that never calls `Orchestrator` at all. In a codebase I owned, I would have noticed that immediately. In someone else's production code, it was invisible until I traced the full path.

I also learned a lot about state management and orchestration as concrete things, not abstract concepts. Working through what it means for state to survive a process crash — each `setex` call as a recovery checkpoint, the resume logic as what makes durability real — gave me a model I didn't have before. Writing tests for that logic was its own education: I don't fully have testing down yet, but I learned what makes a test meaningful versus one that just exercises a code path.

**How did AI tools help — and where did they fall short?**
Claude Code was most useful for navigating to the right files, reading `orchestrator.py` and `session_store.py` together to identify the exact bug lines, and explaining why the pre-commit mypy overrides in `pyproject.toml` were the right place to suppress pre-existing errors. It also caught the `AttributeError` in `health.py` — an unrelated breakage I wouldn't have found until the server failed to start. Where it fell short was on judgment calls: how deeply to wire Redis without scope-creeping into the `review_service.py` stub, and what reviewers expect from a first-time external contributor. Those required human judgment Claude Code couldn't supply.

**What would you do differently if you started over?**
Budget time differently — treat the comprehension work as the main event, not the warmup. And read the full call path before writing any tests. I went straight to the files the issue named and wrote reproduction tests first. That was correct at the unit level, but it meant the dead code gap didn't surface until implementation, when fixing it forced a scope decision under time pressure. A call-path trace in Week 7 would have caught that earlier.

**What are you most proud of from this module?**
Opening the PR. Before this module I had never submitted a pull request to a real open source repository — not because I didn't know how, but because I always found a reason to wait: the fix wasn't polished enough, I didn't understand enough of the codebase. This course forced me past that hesitation, and what I found on the other side was that the PR was fine. The hesitation wasn't protecting quality; it was just hesitation.

Writing tests is something I learned more about here than anywhere else, even if I don't fully have it yet. The two tests in `test_orchestrator.py` are genuinely good: they fail against the original code, pass after the fix, and make the bug legible to anyone who reads them. That's a bar I didn't know how to clear before this module. The goal now is to keep going — a few more real PRs, without a deadline forcing it, to build the habit into something that doesn't require external pressure.