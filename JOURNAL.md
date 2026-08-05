## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No — still awaiting review

**Summary of feedback:**
[What did reviewers comment on? Or note that no review came in.]
No reviews came in.

**How you responded:**
[What changes did you make, or what did you reply? If no feedback,
leave blank.]

---

### Reflection

**What was harder than you expected?**
Probably dealing with git, and the size of the repository, together. While I am usually pretty
confident with git, it was a little challenging to deal with failed tests (and therefore 
dealing with git not letting me commit). I have never encountered that before, so it was 
definitely a learning curve.

**What did you learn about working in a large codebase?**
Personally, I think I understood on a deeper level why it is so important to have an organized 
directory in your project. It would be a lot harder to navigate in someone else's production 
code if there was no organization and no comments. So that helped a lot and made me appreciate it. 
So, I think that contributing to your own project is easier for that reason. But in the real world, you never 
really contribute only to your own codebase - you always work with someone else. 
So, it was good practice to try and navigate in someone else's code.

**How did AI tools help — and where did they fall short?**
To be honest, AI helped a lot with rewriting my docs. As an engineer, it has always been a little challenging
for me to write well, and AI rephrasing and polishing my thoughts was really helpful. Additionally, I think the
AI was very helpful explaining the functions or files (e.g. I would ask: what does this file do? - and AI 
would summarize it). I think I still had to rely a lot on my own knowdlege, as AI always tried to complicate 
things. For example, when git would fail to commit because of the failed checks, AI wanted to fix it 
immediately, but I really needed was how to commit without running the checks at all, not fixing the problems themselves.

**What would you do differently if you started over?**
[Issue selection, planning, implementation, or process — anything
you'd change?]
I think that I would probably pick a higher tier issue. I picked tier 1 issue because I have never contributed
to an open source before. Looking back, I should have known that it isn't much different from contributing to 
any other repository with its own rules (in my opinion). Tier 1 issue that I picked was basically a one-line 
fix, and I wish I could do more coding/problem-solving. Other than that, I think everything else went smooth.

**What are you most proud of from this module?**
I think I am most proud of being able to use git with confidence. I think that git is a skill, and no one can
just master it once and forget - it requires constant practice and refreshing. I was able to handle most of the
git I needed to use on my own, without using AI. That makes me very happy.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
I've implemented the core fix. Progress against the sub-tasks in PLAN.md:

1. **Confirm instantiation** — Done. Traced where `Orchestrator`/`SessionStore` are created in the API layer. It was a useful sanity check but ended up not mattering for the fix, so no code changed here.
2. **Fix state handling in `run()`** — Done (uncommitted). In `agent/orchestrator.py` I removed the line that loaded and merged the previous session (`session_state = self.session_store.get(profile_id) or {}`), so `session_state` now starts empty and only the current review's `results` are persisted. Each review is treated as fresh.
3. **Add regression test** — In progress. The Week 8 reproduction (`tests/repro_43.py`) exists; still need to add a proper regression test in `tests/unit/test_orchestrator.py` asserting no stale keys remain after a two-review (project present → removed) scenario.
4. **Run checks** — Not started. Need to run `make test-unit` and `make check` (lint/format/typecheck).
5. **Document** — Week 8 is updated with the reproduction commit link and PLAN.md link; will update Check-in 2 once the PR is open.

**Next steps:**
- Add the regression test for the two-review scenario (step 3).
- Confirm whether `self.context_manager` also needs resetting at the start of `run()` — the plan flagged it as a possible second source of stale results.
- Run `make test-unit` and `make check`, then commit the orchestrator fix and open the PR.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/798

**Branch:** `fix/43-agent-session-state-not-cleared-between-reviews`

**What you built:**
`Orchestrator.run()` used to load the previous review's session state from Redis and merge new results over it, so tool results from an earlier review (e.g. `github_tool` for a project the user later removed) lingered in the stored session. The fix treats each review as a fresh analysis: it no longer loads prior state, so only the current review's tool results are persisted and removed/changed portfolio data is no longer reflected as stale.

**Tests added or updated:**
Added `tests/unit/test_orchestrator.py` with regression coverage for issue #43. The key test (`test_removed_project_leaves_no_stale_state`) runs two reviews for the same user — one with a GitHub project, then one after the project is removed — and asserts no stale `github_tool` result survives. It was confirmed to fail before the fix and pass after. Also covers the first-review, updated-content, and no-session-store edge cases.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Baseline before my change: `ruff` 182 errors, `mypy agent/` 18 errors, `pytest tests/unit -m unit` 53 failed / 375 passed — all pre-existing and unrelated to this issue. After my change: no new lint, type, or test failures, and my 4 new tests pass. Per the "documented pre-existing failures" guidance, "passes" means my changes introduce no new failures.)

**Draft PR feedback received from:** pending (PR shared for review; will update with reviewer name/Slack handle)

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [\[Commit Link\]](https://github.com/zhannasunny/pathreview/commit/88e64c45e148a38c522007271bdf89738b70c4f9)

**Reproduction summary:**
Ran `Orchestrator.run()` twice for the same `profile_id` using an in-memory fake Redis and stub tools: review 1 with a GitHub project + README, then review 2 after removing the project. The stale `github_tool` result from review 1 was still present in the stored session after review 2, because `run()` loads the previous state and does `session_state.update(results)` instead of clearing it — confirming the bug.

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** 

**Blockers or open questions:**
Need to confirm how the API layer instantiates `Orchestrator`/`SessionStore` — whether a single `Orchestrator` (and its `ContextManager` memoization cache) is reused across reviews, which would be a second source of stale results beyond the Redis merge.

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The bug is that the agent keeps reusing old session data for the same user instead of treating each new review as a fresh analysis. In the current flow, the session cache in session_store.py and the orchestration logic in orchestrator.py can preserve stale tool results across reviews, so updates to a user’s portfolio are not fully reflected. A successful fix would ensure that previous review state is cleared or invalidated when a new review starts, allowing the agent to rerun the relevant tools and produce up-to-date results.

**Branch name:** fix/43-agent-session-state-not-cleared-between-reviews

**Setup confirmation:** [YES] App runs locally at localhost:5173

**Cohort ledger:** [YES] Issue added to cohort ledger