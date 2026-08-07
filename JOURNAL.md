## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/37

**Issue title:** Add snapshot tests for prompt templates to catch accidental changes

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `rag/generator/prompt_templates.py` module holds versioned prompt templates used by the review generator, but nothing currently enforces that changes to a template are accompanied by a version bump. A developer can silently edit the text of `v1` (or any existing version) and the app will keep running, quietly shipping different LLM behavior. The existing `tests/unit/test_prompt_templates.py` has a placeholder "snapshot" test that only checks the length of a hash string, so it does not actually catch content changes. A successful fix adds real per-template hash snapshots so that any modification to an existing version fails the test suite, forcing developers to add a new version (e.g., `v2`) instead of silently mutating `v1`.

**Branch name:** feat/37-prompt-template-snapshots

**"Is this right for me?" reasoning:**
Scope matches the Tier 1 estimate (3–5 hours) — I finished in ~4 hours.
Skills align well: I already work with LLM prompt templates and
evaluation in my own research, so understanding what "silent template
drift" means and why version pinning matters was intuitive. No new
libraries needed — the fix uses stdlib `hashlib` and existing `pytest`,
so I didn't need to learn a snapshot testing framework from scratch.
The blast radius is contained to one test file, which makes it low-risk
for a first contribution.

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/natanyanderson/pathreview/commit/a7d77a8aaf2f5b83fcddb48f059f404de31dc2a0

**Reproduction summary:**
Verified in the local checkout that the placeholder
`test_template_snapshot_content_hash` in
`tests/unit/test_prompt_templates.py` cannot detect template drift: it
only asserts that an MD5 hex digest is 32 characters long, which is
always true. Confirmed by editing
`PROMPT_TEMPLATES["skills_feedback"]["v1"]` and re-running the test —
it still passed, proving no protection existed.

**PLAN.md link:** https://github.com/natanyanderson/pathreview/blob/feat/37-prompt-template-snapshots/PLAN.md

**Walkthrough video (recommended):** [skipping — will do office hours if needed]

**Blockers or open questions:** None. PR #301 is already open and passing tests locally.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Fix is fully implemented. Both new tests
(`test_template_content_matches_snapshot` and
`test_every_template_version_has_a_snapshot`) are passing, and the
placeholder `test_template_snapshot_content_hash` has been removed.
All 38 tests in `tests/unit/test_prompt_templates.py` pass locally.
The PR is open at #301 and I'm treating this week as review + polish
rather than new implementation, since sub-tasks 1–5 in PLAN.md are
already complete.

**Next steps:**
Run the full `make check` and `make test-unit` suites, document any
pre-existing failures in the PR description, request peer feedback in
Slack, and address any review comments before the deadline.

**Blockers:**
None right now. Only open question is whether reviewers will want me
to also fix the pre-existing ruff/mypy violations in
`test_prompt_templates.py`. I've left those alone to keep the diff
scoped, but I'll fold them in if requested.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/301

**Branch:** feat/37-prompt-template-snapshots

**What you built:**
Replaced the placeholder `test_template_snapshot_content_hash` in `tests/unit/test_prompt_templates.py` with real per-template SHA-256 snapshots. Added two new pytest tests: `test_template_content_matches_snapshot` fails when a registered template's content changes without a version bump, and `test_every_template_version_has_a_snapshot` catches the reverse case of adding a new template without a registered snapshot. This gives the project actual regression protection against silent prompt drift.

**Tests added or updated:**
Modified `tests/unit/test_prompt_templates.py`. Removed 1 placeholder test, added 2 real snapshot tests plus an `EXPECTED_TEMPLATE_SNAPSHOTS` dict pinning all 5 current template versions. All 38 tests in the file pass locally. Manually verified the snapshot test catches drift by editing `PROMPT_TEMPLATES["skills_feedback"]["v1"]` character-by-character and confirming the test fails with the expected error message, then reverting to confirm it passes again.

**Self-review confirmation:** [ ] make check passes  [ ] make test-unit passes

Note on `make check`: the codebase has ~176 pre-existing ruff/mypy violations across many files. `test_prompt_templates.py` specifically had 14 errors on `main` and 13 after my changes — my contribution removed 1 error and introduced 0 new ones.

Note on `make test-unit`: 53 pre-existing test failures across the project on `main` (in files like `test_structural_chunker.py`, `test_tech_detector.py`, `test_review_service.py`). Confirmed the identical 53 failures exist on `main` before my changes via `git stash`. In `tests/unit/test_prompt_templates.py` specifically — the file I modified — all 38 tests pass, including both new snapshot tests. Per the Week 9 "doesn't make things worse" guidance, my contribution introduces 0 new test failures and 0 new lint errors.

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x0] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in during the module (per the Summer 2026 cohort note, reviewer feedback is not a course feature this term). The PR is open at ascherj/pathreview#301 and passing all tests in the file it touches.

**How you responded:**
N/A — no feedback to respond to. If a maintainer comments after the module closes, I plan to keep engaging with the PR until it either merges or the maintainers decide against it.

---

### Reflection

**What was harder than you expected?**
Setup was the biggest surprise. Getting the local environment running was a full afternoon of dependency debugging that had nothing to do with my actual issue — chromadb required an older Python because of onnxruntime, the setup script assumed Docker was already running when it wasn't, and I had a stale `.venv` from a previous failed run that kept masking the real errors. I went into Week 7 expecting to spend most of my time reading code and picking a good issue, and instead I spent most of it fighting the Python + Postgres + Docker stack before I could even run the app. In hindsight this is probably normal for any real codebase, but it was a shift from how "getting started" works on my own projects, where I control every layer.

**What did you learn about working in a large codebase?**
The biggest lesson was that "the fix" and "the scope of what to touch" are separate decisions. When I ran `make check` on my final PR, the file I edited had 13 lint errors and the whole project had 176 — but only 1 error was actually caused by my changes, and my fix removed one pre-existing error rather than adding new ones. Early in the week I assumed I had to fix everything the linter complained about; by the end I understood that a well-scoped PR fixes the thing it says it fixes and explicitly documents the pre-existing violations rather than expanding to cover them. That framing ("doesn't make things worse" vs. "fixes the whole codebase") is very different from how I work in my own projects, where I own every line.

I also learned to read tests as documentation. The existing tests in `test_prompt_templates.py` were the fastest way to understand what the prompt template system was supposed to do — faster than reading `prompt_templates.py` itself. That surprised me.

**How did AI tools help — and where did they fall short?**
AI was most useful for the mechanical parts: writing the initial docstring/error-message copy for the new tests, formatting the JOURNAL and PLAN files consistently, and pattern-matching against existing test structure in the file. It was reliably fast for that kind of work.

Where it fell short was scope judgment. When my commit was blocked by pre-commit hooks with ~50 lint/type errors, my first instinct (and the AI's first suggestion path) was to "just fix them all." That would have been wrong — most were pre-existing and out of scope. I had to make the call myself to compare error counts before and after my changes and prove I wasn't making things worse. AI is good at "how do I do X" and much weaker at "should I do X in this context."

The other place AI fell short was on the specific mental model of "silent test that passes because the assertion is a tautology." The failing test wasn't hard to spot once I read it, but understanding *why* it was designed to fail loudly — and how to write a replacement that actually enforced the contract the docstring implied — required thinking about the intent behind the code, not just its syntax.

**What would you do differently if you started over?**
Two things.

First, I'd spend less time on issue selection. I got a bit stuck comparing three candidate Tier 1 issues (async mocks, README scorer fixture, faithfulness None-handling) and worrying about who else had "claimed" them on GitHub. In retrospect, most of those claims were from months ago with no follow-up PRs, and my TF explicitly said multiple people can work on the same issue in this course. I could have started on a good issue on Day 1 instead of Day 2 or 3.

Second, I'd verify my environment with `make setup && make run` before doing any of the ancillary Week 7 steps (JOURNAL, PLAN, branch naming). Getting the app running is the single most important gate, because if you can't run it, you can't verify anything else. I did steps like "create branch" and "make initial commit" in parallel with debugging setup, which meant some of my early commits were on a branch where setup wasn't actually working yet.

**What are you most proud of from this module?**
The sanity check I ran on my snapshot test. After I wrote the two new tests and they passed, it would have been easy to stop there — 38/38 green, PR opens itself. Instead I opened `prompt_templates.py`, changed one character in a template, re-ran the test, and confirmed it failed with the exact error message I'd written telling the developer to add a new version. Then I reverted and confirmed it passed again. That two-minute exercise — proving the test actually does what its name implies — is the thing I'll carry forward into future work. It's a habit I didn't really have before this module.