## Week 7 — Issue selection

**Issue link:** https://github.com/jamjamgobambam/pathreview/issues/91

**Issue title:** Review page shows a blank section when the confidence field is below 0.3 instead of a warning badge

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The ReviewSection component is supposed to display a "Low confidence" badge whenever a review's confidence score falls below 0.3, warning users that the result may be unreliable. At some point the conditional logic that renders this badge was removed, so instead of a warning, the component renders an empty div — the section just looks broken or missing. A successful fix restores the conditional rendering in ReviewSection.tsx so the badge appears correctly whenever confidence is below the threshold, and the section renders normally otherwise.

**Branch name:** fix/91-review-section-confidence-badge

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger — link not yet located; posted in Slack asking for it

**Note:** Issue #91 was later closed/removed by instructor feedback. Pivoted to a new issue (#159) starting Week 8 — see below.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/saharii27/pathreview/commit/c64f2f5

**Reproduction summary:**
Ran `.venv/bin/pytest tests/unit/test_batch_processor.py::TestBatchEmbeddingProcessor::test_empty_chunks_list_returns_empty -q` and confirmed the failure: the warning log "Empty chunks list provided to BatchEmbeddingProcessor" is clearly printed to stdout, but `caplog.text` is empty, causing the assertion to fail. This confirms structlog output isn't propagating into Python's standard `logging` module, which is what pytest's `caplog` fixture reads from.

**PLAN.md link:** https://github.com/saharii27/pathreview/blob/fix/159-structlog-caplog-pytest/PLAN.md

**Walkthrough video (recommended):** [not recorded — optional, not graded]

**Blockers or open questions:**
Need to determine the cleanest way to configure structlog to propagate to stdlib logging in tests/conftest.py — likely via structlog.stdlib processors or the capture_logs context manager.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Root cause identified: structlog was never configured to propagate into stdlib logging during test runs, since `configure_logging()` was only called from `scripts/seed_db.py`, not from any test setup. Implemented the fix as an autouse, session-scoped fixture in `tests/conftest.py` that calls `configure_logging()` before tests run. Confirmed the originally failing test (`test_empty_chunks_list_returns_empty`) now passes. Added a new dedicated test (`test_logging_config.py`) that directly verifies structlog output reaches `caplog`. Full suite re-run confirms no new failures introduced (52 failed / 377 passed, down from 53 failed / 375 passed) and `make check` shows the same 182 pre-existing lint errors before and after. Opened draft PR: https://github.com/ascherj/pathreview/pull/661

**Next steps:**
Request peer/mentor feedback on the draft PR via Slack. Address any feedback received, then mark the PR ready for review and complete Check-in 2 by Sunday's deadline.

**Blockers:**
None currently.



## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No feedback was provided. Per course guidance, reviewer feedback is not a feature in Summer 2026.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Picking the right issue turned out to be much harder than I expected. My first choice (#107) looked like a clean, well-scoped bug, but another student's comment thread revealed it didn't actually reproduce — the code it referenced didn't even exist in git history. My second choice (#159) reproduced perfectly, but I later found 9+ other students had already claimed and started work on the same issue on a shared class fork. I assumed picking an issue would be a quick, mostly mechanical step; instead it took real investigation — reading full comment threads, not just titles and tags — before I could commit with confidence.

**What did you learn about working in a large codebase?**
The biggest lesson was that tests reveal intent and behavior better than the code itself does. When I was trying to understand why `caplog` wasn't capturing structlog output, reading the actual test assertions (what the test expected to see vs. what it actually got) told me more about the intended behavior than reading `core/logging.py` in isolation. Tests acted like a spec for what the original developers meant the system to do, which made the codebase far more navigable than just reading source files top to bottom.

**How did AI tools help — and where did they fall short?**
AI tools were most useful for debugging errors and tracebacks — every time I hit a wall (the numpy/ChromaDB architecture mismatch, the `vite: command not found` error, the mypy type annotation failures, the pytest marker deselection issue), being able to paste the raw error and get a targeted explanation of root cause saved enormous amounts of time compared to searching piecemeal. Where it fell short was judgment calls that required real investigation rather than pattern-matching — like actually reading through 9 comments on issue #159 to decide whether it was still worth claiming. That required me to read and reason through the actual thread myself; no shortcut replaced doing that work directly.

**What would you do differently if you started over?**
I'd pick my issue faster, with less back-and-forth. I spent a lot of time cross-referencing comment counts, tier labels, and issue descriptions across two different forks before settling on #159. In hindsight, I'd set a firmer time-box on issue selection — skim the full thread once, make a decision, and move on, rather than second-guessing across multiple rounds of comparison.

**What are you most proud of from this module?**
Getting through the Docker/environment setup mess. Between Docker Desktop not being installed at all, the ChromaDB/numpy architecture incompatibility on Apple Silicon, the missing `npm install` step, and a stuck Postgres migration from an earlier failed run, there were multiple points where nothing was working and it wasn't obvious why. Working through each error methodically — reading tracebacks carefully rather than guessing — and eventually getting a fully working local environment felt like the most real, transferable skill from this whole module.
