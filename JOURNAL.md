Week 7 — Issue selection

Issue link: https://github.com/ascherj/pathreview/issues/153

Issue title: Faithfulness checker crashes when a context chunk has text: None

Tier: [x] Tier 1  [ ] Tier 2  [ ] Tier 3

Problem summary:
The RAG system's faithfulness checker verifies that generated review feedback is actually supported by the retrieved context chunks. When building that context, it pulls each chunk's text using chunk.get("text", ""), assuming a missing key falls back to an empty string, but a dict's .get() only applies the default when the key is absent, not when the key exists with a None value. If any chunk in the context has text: None (rather than a missing text field entirely), the subsequent string-join over all chunk texts crashes with a TypeError instead of gracefully treating it as empty. A successful fix would normalize None text values to an empty string (or filter them out) before joining, so the faithfulness checker degrades gracefully instead of crashing when upstream ingestion produces a chunk with no text.

Branch name: fix/153-faithfulness-checker-none-text

Setup confirmation: [x] App runs locally at localhost:5173

Cohort ledger: [x] Issue added to cohort ledger 

Issue fit and selection reasoning:

Understanding the issue: chunk.get("text", "") returns None instead of the default when the "text" key exists but is set to None, so the later " ".join(...) crashes with TypeError. Before the fix, any chunk with text: None crashes faithfulness scoring; after, it returns a normal float score and the existing test_none_context_chunk_text test passes.

Tier fit: First open source contribution, so Tier 1 is the deliberate choice, matching the issue's own tier-1 / good first issue labels. The fix is confined to one function in one file, no API, ingestion, or DB changes involved.

Codebase readiness: Read FaithfulnessChecker.check() and its helpers, confirmed the bug is isolated to the context_chunks-to-context_text join and won't affect claim-extraction or overlap logic downstream. Fix: chunk.get("text") or "". Read the test file end-to-end; test_none_context_chunk_text already targets this exact case, and test_missing_text_key_in_chunk confirms the missing-key case already works, so both need to behave the same way.

Scope and time: PR #162 is already open on this issue; claims are non-exclusive, so proceeding but will check that PR first. Estimate 3-4 hours (reproduction, fix, tests, PR), within Tier 1's 3-6 hour range and the Week 8-9 window. No blockers noted.

Week 8 — Reproduction & solution planning

Reproduction commit link: https://github.com/jasmitha-alle/pathreview/commit/92e141ee7bb3f53e858607f0f57c509bbd7f87e4

Reproduction summary: Called FaithfulnessChecker().check("Knows Python.", [{"text": None}]) directly in a Python shell and observed the exact crash described in the issue: TypeError: sequence item 0: expected str instance, NoneType found, raised from the " ".join(...) call on context_chunks. Documented the reproduction with a comment at the bug site in rag/evaluator/faithfulness_checker.py.

PLAN.md link: https://github.com/jasmitha-alle/pathreview/blob/fix/153-faithfulness-checker-none-text/PLAN.md

Walkthrough video (recommended): [not recorded]

Blockers or open questions: PR#162 is already open against this issue, need to check whether it already resolves the bug before finalizing my own fix approach.

Week 9 — Solution building & PR submission

Check-in 1 (mid-week)

Current progress: Implemented the fix for issue#153, changed chunk.get("text", "") to chunk.get("text") or "" in rag/evaluator/faithfulness_checker.py so both a missing text key and an explicit None value normalize to an empty string. Added a new test, test_mixed_none_and_valid_text_chunks, covering a mixed list of None and valid-text chunks. Captured a full pre-existing-failures baseline (make test-unit, make lint, make format, make typecheck) before making changes, confirmed the fix introduces no new failures, and opened a draft PR (#748) against ascherj/pathreview.

Next steps: Get peer/mentor feedback on the draft PR in Slack, address any requested changes, then mark the PR ready for review and do a final self-review pass before Sunday's deadline.

Blockers: None currently. One thing I'm keeping an eye on: PR#162 is already open against issue#153, will check it doesn't conflict before finalizing.

Check-in 2 (end of week)

PR link: https://github.com/ascherj/pathreview/pull/748

Branch: fix/153-faithfulness-checker-none-text

What you built: Fixed a crash in FaithfulnessChecker.check() where a context chunk with text: None caused an unhandled TypeError during string joining. Normalized both missing and explicitly-None text values to an empty string so the checker degrades gracefully instead of crashing.

Tests added or updated: Added test_mixed_none_and_valid_text_chunks to tests/unit/test_faithfulness_checker.py. The existing test_none_context_chunk_text (previously failing) now passes.

Self-review confirmation: make check passes, make test-unit passes, both confirmed passing for the files this PR touches; pre-existing unrelated failures across the rest of the codebase are documented in the PR description and unaffected by this change.

Draft PR feedback received from: none



Week 10 — Iteration & reflection

Reviewer feedback

Feedback received: No — reviewer feedback isn't a feature this semester (Su26), per the course note. No maintainer comments came in on PR#748.

Summary of feedback: N/A — not applicable per the Su26 course note on reviewer feedback.

How you responded: N/A.

Reflection

What was harder than you expected? 
Getting the environment running ate far more time than the actual code fix. Between a venv creation that got interrupted mid-ensurepip, Docker Desktop not running, a missing .env file, and Node/npm not being installed at all, I spent longer on make setup than on the one-line fix in faithfulness_checker.py. The actual bug (chunk.get("text", "") returning None instead of a default) took minutes to understand and fix once I could run the code at all. I also didn't expect make format to silently reformat 47 unrelated files across the whole repo, I almost committed a massive, out-of-scope diff without realizing black doesn't scope itself to just the files I'd touched.

What did you learn about working in a large codebase? 
The most important skill wasn't reading code, it was telling the difference between "my bug" and "pre-existing noise." Before touching anything, I ran make test-unit, make lint, and make typecheck to capture a baseline: 53 failing tests, ~180 lint errors, and 5 mypy errors that had nothing to do with my issue. Without that baseline, I wouldn't have been able to tell a reviewer with confidence that my fix introduced zero new failures, I'd have just been guessing. I also learned that a project's own tooling config can be internally inconsistent: the Makefile's typecheck target deliberately excludes tests/, but the pre-commit mypy hook checks it anyway, which blocked my commit over 26 pre-existing "missing annotation" errors I had nothing to do with. A newcomer can't know that from reading docs, you only find it by hitting the wall.

How did AI tools help, and where did they fall short?
 AI was fastest at diagnosis: explaining why pytest hung on pytest-benchmark's git call. It fell short anywhere I required more analysis to be done. There was also a moment where AI told me a fix was missing from GitHub when it wasn't, it had hit a stale CDN cache on raw.githubusercontent.com and I had to ask it to double check with local grep before trusting that. That was a good reminder that AI's read of "what's true" is only as good as the data it just fetched, and it can be wrong with full confidence.

What would you do differently if you started over?
 I'd capture the pre-existing failure baseline at the very start of Week 8, before writing PLAN.md, instead of doing it late in Week 9. Having those numbers earlier would have made my plan's "risks and unknowns" section sharper. I'd also read the actual grading rubric and PR template before drafting anything, instead of writing a generic version first and then rewriting it once I saw what was actually being graded.

What are you most proud of?
 Not the fix itself, it's one line. I'm most proud of catching that 3 of the 4 failing tests in test_faithfulness_checker.py were unrelated to my bug before I assumed my fix was incomplete. It would have been easy to either panic and try to "fix" tests that weren't mine to fix, or to just ignore the discrepancy. Checking each failing test's actual input (none of the three passed a None value) before drawing a conclusion is the habit I want to keep from this module.

