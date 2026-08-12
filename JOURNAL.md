## Week 7 — Issue selection

**Issue link:** (https://github.com/ascherj/pathreview/issues/66)

**Issue title:** Safety monitoring doesn't emit metrics when the content filter is bypassed by a multi-turn conversation
 

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**

Issue number 66 talks about dealing with flaged conversation as a whole, and not one prmopt. It asks us to create SafetyMonitor.get_event_count tool that goes along the conversation and collect the flagged words and see if it should kick the user or the materils that is being requested is safe. 

One way to solve it as I can see is to implement window_hours currently, which means it is getting all the events rather than within the last 1 hour.

The codebase shows a hardcoded review with no AI generation integrated even and the clear solution is adding the safety monitor and providing multi-turn support.

**Branch name:** fix/66-safety-monitor-multi-turn-metrics
https://github.com/aliabbaka/pathreview/blob/fix/66-safety-monitor-multi-turn-metrics/JOURNAL.md
**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/aliabbaka/pathreview/commit/3e041c75750ed1bcc1236005ed38f7c139b4ad7a

**Reproduction summary:**Added a failing unit test (test_monitoring.py::test_window_hours_is_ignored_reproduces_66) that records 5 lifetime content_filtered events with only 2 inside the last hour, then calls get_event_count("content_filtered", window_hours=1). It returns 5 instead of 2 (assert 5 == 2 fails), confirming window_hours is ignored so events across a multi-turn conversation are never counted within a rolling window.
**PLAN.md link:** https://github.com/aliabbaka/pathreview/blob/fix/66-safety-monitor-multi-turn-metrics/PLAN.md

**Walkthrough video (recommended):** https://drive.google.com/file/d/1S-X-YzFoySNWFty719cXwbFFI_7OrP8A/view?usp=sharing
**Blockers or open questions:**
If there could be a bigger time frame, more than two hours but that will not increase the latency of the answers.


## Week 9 — Implementation & review (mid-week)

**Fix commit link:** https://github.com/aliabbaka/pathreview/commit/02bd06f

**What I built:** Switched `SafetyMonitor` from a cumulative `INCR` counter to a
Redis sorted set of timestamped events. `get_event_count` now enforces `window_hours`
via `zremrangebyscore` + `zcard`, mirroring `RateLimiter`. The reproduction test
(`test_window_hours_is_ignored_reproduces_66`) now passes; added 3 tests (timestamped
write, windowed count, error path) and hardened the unknown-type test. `ruff`/`black`/
`mypy` clean on changed files; 5/5 monitoring tests pass.

**Draft PR:** https://github.com/ascherj/pathreview/pull/1022

**Blockers or open questions:** Whether wiring `get_event_count` into the content-filter
path (PLAN §3.3) should be part of this issue or a separate follow-up. `SafetyMonitor`
currently has no callers.


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No peer review has come in yet. PR #1022 is open as a draft and posted for review; I'll
update this section with the reviewer's comments once they land, then flip the PR from
Draft to "Ready for review" after addressing them.

**How you responded:**
No feedback yet, so no changes made in response. Pending review.

---

### Reflection

**What was harder than you expected?**
Two things I didn't see coming. First, the repo is seeded with dozens of intentional
bugs, so running `make test-unit` showed 56 failures — it looked like I'd broken
everything, and it took a moment to realize almost all of those belonged to other
issues, not mine. Learning to run just `tests/unit/test_monitoring.py` and judge my work
by *that* was the real skill. Second, Git hygiene tripped me up: a stray full copy of the
project had been cloned inside itself (`pathreview/pathreview/`) which blocked commits,
and at one point my fix and tests got bundled into a single commit mislabeled `test(...)`
instead of a proper `fix(...): Fixes #66`. Cleaning that up mattered more than I expected.

**What did you learn about working in a large codebase?**
Scope discipline is everything. In my own project I can change anything; here the right
instinct is to touch only my module, match the conventions already in the code, and not
"fix" things outside my issue. The cleanest part of my fix was that I didn't invent a new
approach — I copied the rolling-window sorted-set pattern already used in
`rate_limiter.py`, so `monitoring.py` now reads like the code around it. I also learned to
separate *my* test failures from the pre-existing ones instead of panicking at a red suite.

**How did AI tools help — and where did they fall short?**
AI was strongest at navigation and drafting: mapping where the bug lived, pointing me at
the `RateLimiter` pattern to mirror, and drafting the Conventional Commit messages, PR
body, and these journal entries. It fell short on anything outside the code — it couldn't
open the PR or run the Slack review (the `gh` CLI wasn't even installed), and the genuinely
judgment-based calls were mine: deciding that wiring `SafetyMonitor` into the content
filter (PLAN §3.3) should be a follow-up rather than scope-creep in this PR.

**What would you do differently if you started over?**
Commit in small, correctly-labeled steps from the very beginning instead of having to
`reset --soft` and re-split later. I'd also clean up the environment (the nested duplicate
repo) before starting, and decide the scope boundary (§3.3 in or out) up front in PLAN.md
so it didn't stay an open question all the way to the PR.

**What are you most proud of from this module?**
The reproduction-first workflow. I wrote a failing test that pinned the exact bug —
`window_hours` being ignored so a 1-hour and a 1000-hour window returned the same count —
before touching the implementation, then watched it flip from red to green once the fix
landed. Seeing that single assertion go from `5 == 2` failing to passing made the whole
fix feel provable rather than hopeful.