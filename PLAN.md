## Solution plan

**Issue:** [https://github.com/ascherj/pathreview/issues/43]

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

**Root Cause**

The issue's root cause is misattributed; the fix cannot live purely in `session_store.py`. The genuine staleness risks lives in the caching layer - `market_analyzer`'s constant input combined with `ContextManager` memoization on a reused `Orchestrator`. A separate, _latent_ data-hygiene issue is the accumulating `session_state.update()` merge in `orchestrator.py`. 

**Actual Behavior**
The ochestrator issues and executes a call for every tool in the plan and never consults `session_store` to skip execution. The only cache check is in the in-memory `ContextManager`. The loaded session state is merged via `session_state.update(results)` and re-saved, but `run()` never serves `session_state` so this becomes a latent data-hygiene issue rather than the reported bug; `session_store.delete()` is never called, so no reset happens. The real staleness occurs only when two conditions hold together: a single `Orchestrator` instance is reused across reviews (so it's `ContextManager` persists), and a tool's input hash is portfolio-independent - exactly `market_analyzer`, whose input is the constant `{"detected_skills": {}}` at `orchestrator.py:130`. Under those conditions the second review replays the cached first-review result instead of re-running.

**Expected:**
A review must always reflect the portfolio submitted for _that_ review; a cached result may be reused only for identical input. The fix belongs in the caching layer (`ContextManager` + `orchestrator.py`), not `session_store.py`:
1. **Scope the cache to a single run** - reset `ContextManager` at the start of `run()`), so a reused `Orchestrator` can't replay a previous profile's results - **or** include a portfolio content-hash/version in the memo key so changed input missed the cache.
2. **Fix `market_analyzer`'s input** in `orchestrator.py` so it's populated from the actual detected skills instead of the constant `{"detected_skills":{}}`; otherwise its memo key can never distinguish an old portfolio from a new one. 

Optionally, invalidate persisted session state on a new review (`session_store.delete())` or version-keyed replace) to clear the latent merge accumulation - a hygiene improvement, not the core fix. 


### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
**Files I plan to touch:**
- `agent/orchestrator.py` - core fix
- `agent/memory/context_manager.py` - cache reset/keying (core)
- `tests/unit/test_orchestrator.py` - flip the fix-target test, retire the repro test
- `agent/memory/session_stoer.py` - *optional*; only for the hygiene invalidation

**Functions / methods:**
- `Orchestrator.run()` - reset the `ContextManager` per run; assemble `market_analyzer`'s input from detected skills
- `Orchestrator._build_plan()` - source of the {"detected_skills: {}}` constant (orchestrator.py:130)
- `Orchestrator._execute_tool()` - only if versioning the memo key (the memoization call lives here)
- `ContextManager.clear()` - only if resetting the cache per run; otherwise `store_tool_result` ' `get_tool_result`


### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. **Feed `market_analyzer` real detected skills:**
    In `Orchestrator` (`_build_plan` / `run`), replace the constant `{"detected_skills": {}}` with skills derived from the portfolio (i.e from the `tech_detector` / `skill_extractor` output). This makes its memo key vary with the portfolio instead of being identical every review. 
2. **Scope the cache to a single review**
    Add  `ContextManager.clear()` and call it at the start of `Orchestrator.run()`, so a reused `Orchestrator` instance cannot replay a previous portfolio's cached results. **or** Include a portfolio content-hash in the memo key via `hash_input` / `execute_tool` instead of clearing. 
3. **Update the tests**
    Remove the `@pytest.mark.xfail` from `test_reused_orchestrator_reruns_with_real_skills_after_fix` and confirm it passes; retire (or `xfail`) the now-obsolete `test_reused_orchestrator_replays_stale_market_result`, which documented the old buggy behavior. 
4. **Verify**
    Run `make test-unit` and `make check` before committing

### Inputs & outputs
What does your fix take as input? What should it produce or change?

**Input**
`Orchestrator.run(profile_id, profile_data)` - the user's portfolio (`files`, `readme_content`, `resume_text`, `github_username`, etc.). The fix also consumes the skills detected by earlier tools in the plan. 

**Output**
- `market_analyzer` receives real portfolio-derived `detected-skills` instead of the constant `{}`, so its memo key varies per portfolio.
- `ContextManager` is reset (or portfolio-versioned) each run, so a reused `Orchestrator` returns `tool_results` reflecting the **current** portfolio rather than replaying a prior review's cached results. 
- No change to the shape of `run()`'s return value or to `market_analyzer`'s own logic - only what feeds it and when the cache is cleared.

### Risks & unknowns
What could go wrong? What are you still unsure about?
- **Performance trade-off:** resetting the cache each run means an identical re-review re-reuns every tool (no cross-review reuse). Within-run memoization is still preserved, so the cost is bounded.
- **Unknown data flow:** how `detected_skills` should be assembled and what shape `market_analyzer` expects - the code only says "Will be populated by context." Need to confirm which tool's output is the source.
- **No end-to-end path:** the orchestrator isn't wired into the API, so the fix can only be verified via unit tests, not the running app.

### Edge cases
What inputs or states should your fix handle gracefully?
- **Empty / minimal portfolio:** `_build_plan` only adds `market_analyzer``if plan` is non-empty - the fix must not crash when no skills are detected; an empty `detected_skills` should still produce a valid result.
- **First review (no prior session):** `session_store.get()` returns `None` - already handled by `or {}`; the fix must keep that path working.
- **No session store configured:** `run()` guards with `if self.session_store`; the cache-rest fix must work whether or not Redis is present.
- **Same portfolio re-reviewed:** results must stay correct under either approach (reset -> re-runs; version-key -> cache hit).
- **Tool failure:** a failing tool is still recorded as an error dict - the fix must not swallow or alter that error handling. 