## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/153

**Issue title:** Faithfulness checker crashes when a context chunk has `text: None`

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The faithfulness checker's `check()` method builds context text by pulling the `"text"` key out of each context chunk using `chunk.get("text", "")`. This works fine when the key is missing entirely, since `.get()` falls back to an empty string — but it breaks when the key exists and is explicitly set to `None`, because `.get()` only applies its default for missing keys, not for keys with a `None` value. When that happens, the code tries to join a list of strings that includes a `None`, which raises a `TypeError` and crashes the checker. A successful fix will treat a chunk with `text: None` the same as an empty or missing chunk, so the faithfulness check can run without crashing on this edge case, and the existing test `test_none_context_chunk_text` will pass.

**Branch name:** fix/153-faithfulness-none-context-text

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Scope reasoning:**
I chose a Tier 1 issue since this is my first time contributing to a large, unfamiliar codebase, and Tier 1 issues are scoped to a single file/function rather than requiring system-wide understanding. This issue is well-scoped: the bug is isolated to one function (`check()`) in one file (the faithfulness checker in `rag/`), the root cause is already clearly identified in the issue description, and there's an existing failing test I can use to verify my fix. I estimate this will take 3-6 hours of focused work, which fits comfortably within the Week 8-9 timeline. Several other students are also working on this issue, but since claims are non-exclusive and grading is based on my own submitted artifacts, that doesn't change my choice. There are no blockers or dependencies noted on the issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/jmonarro-ai/pathreview/commit/97e9b0a

**Reproduction summary:**
I ran the existing test test_none_context_chunk_text against the unmodified FaithfulnessChecker.check() method and confirmed it fails with TypeError: sequence item 0: expected str instance, NoneType found, matching the crash described in issue #153. I documented the full command and traceback in REPRODUCTION.md.

**PLAN.md link:** https://github.com/jmonarro-ai/pathreview/blob/fix/153-faithfulness-none-context-text/PLAN.md

**Walkthrough video (recommended):** N/A (skipped - not graded)

**Blockers or open questions:**
None currently. The fix is well-scoped to one line in check(); the main thing I'll verify in Week 9 is that the fix doesn't change scores for any of the other currently-passing tests.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed sub-tasks 1-4 from PLAN.md: fixed the None-handling bug in FaithfulnessChecker.check() by changing chunk.get("text", "") to chunk.get("text") or "", confirmed test_none_context_chunk_text now passes, ran the full test_faithfulness_checker.py suite to confirm no regressions, and manually verified the original TypeError no longer occurs. Also added the planned test_mixed_none_and_valid_context_chunks test.

**Next steps:**
Run make check and make test-unit at the full project level to confirm no regressions outside the faithfulness checker module, then open a draft PR and fill in the PR template.

**Blockers:**
The project has 182 pre-existing make check errors and 53 pre-existing make test-unit failures unrelated to issue #153 (confirmed via git stash before making changes). None of these block my fix, but I will document them transparently in the PR's Notes for Reviewers section.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/592

**Branch:** fix/153-faithfulness-none-context-text

**What you built:**
Fixed a TypeError in FaithfulnessChecker.check() that occurred when a context chunk had {"text": None}. Changed chunk.get("text", "") to chunk.get("text") or "" so both missing and None text values fall back to an empty string instead of crashing the join() call.

**Tests added or updated:**
Updated tests/unit/test_faithfulness_checker.py: confirmed the existing test_none_context_chunk_text now passes (previously failed with TypeError), and added a new test test_mixed_none_and_valid_context_chunks covering a list of chunks where one has None text and another has valid text, asserting the valid chunk still contributes to the score.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

(Both commands pass for the files this PR touches; the project has pre-existing, unrelated failures documented in the PR's Notes for Reviewers section, confirmed via git stash to exist before this change.)

**Draft PR feedback received from:** none — no peer/mentor review available this term (per course announcement); self-reviewed against the pre-submission checklist instead.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review comments arrived on PR #592 by the end of the module. Per the course announcement, reviewer feedback is not a feature this term (Summer 2026) — self-review against the pre-submission checklist was the substitute for this cycle.

**How you responded:**
N/A — no feedback was received to respond to.

---

### Reflection

**What was harder than you expected?**
Getting the local environment running was more work than I expected. I hit a WSL2 install requirement for Docker Desktop, then a real dependency conflict where chromadb's pinned image rebuilt hnswlib against a newer, incompatible numpy at container startup, crashing the vector-db service with AttributeError: np.float_ was removed in NumPy 2.0. I had to add a command override in docker-compose.yml to pin numpy<2 before I could even start on the actual fix. I didn't expect that much of Week 7 to be infrastructure debugging rather than reading code.

**What did you learn about working in a large codebase?**
The biggest difference from my own projects was realizing the codebase already had real, pre-existing problems unrelated to my issue -- 182 make check errors and 53 failing tests on main before I touched anything. I had to learn to isolate exactly which failures were mine, using git stash to compare before and after my change, instead of assuming everything red was something I broke. In my own projects a failing test always means I broke something; here it sometimes just means someone else's code has debt I am not responsible for.

**How did AI tools help -- and where did they fall short?**
AI was most useful for isolating scope quickly. For example, when my new test test_mixed_none_and_valid_context_chunks unexpectedly failed, working through it step by step revealed the failure was caused by a separate pre-existing bug in _is_supported()'s keyword-overlap threshold, not my fix -- the feedback text just needed clearer word overlap with the context. Where it fell short was tasks that required actually running things and reading real output -- I still had to run make check, make test-unit, and read raw tracebacks myself to confirm claims like "182 pre-existing errors" rather than trusting an assumption.

**What would you do differently if you started over?**
I would run make check and make test-unit on a completely clean checkout before doing anything else, even before setup troubleshooting, so I had the full baseline numbers from minute one instead of gathering them mid-way through Week 9. I would also draft my new test's input data more carefully upfront -- my first version of test_mixed_none_and_valid_context_chunks used feedback and context text with only one overlapping word, which failed for an unrelated reason and cost me a debugging detour before I adjusted the wording. If real review had been available this term, I also would have opened a top-level PR comment flagging the _is_supported() scoring bug I found in three other tests, rather than just noting it in Notes for Reviewers -- surfacing it explicitly would have been the more proactive move, even though fixing it was out of scope for #153.

**What are you most proud of from this module?**
I am proud of how I handled the PR's Notes for Reviewers section. Instead of just fixing my one bug and moving on, I actually verified with git stash which of the 53 failing tests and 182 lint errors existed before my change, and documented that precisely instead of vaguely. That felt like the real difference between a student exercise and an actual professional contribution.
