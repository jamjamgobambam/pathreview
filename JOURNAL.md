# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/69

**Issue title:** Add a "feedback tone check" that ensures all generated feedback is written constructively

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
Right now the review generator produces feedback sections with no check on how they read — a section could come out vague, discouraging, or dismissive and still go straight to the user. This issue asks for a tone classification step that runs after generation, using a prompt to judge whether each section is constructive (actionable, specific, encouraging) or not. Sections that fail the check should be rejected and regenerated rather than shown to the user. The fix touches the safety layer (`safety/content_filter.py`) and the generation pipeline (`rag/generator/review_generator.py`), since it needs to hook into the point where feedback sections are produced.

**Branch name:** feat/69-feedback-tone-check

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Is This Issue Right for Me? — scope reasoning:**

*Part 1 — Understanding the issue.* Before the fix, `ReviewGenerator.generate_full_review()` (`rag/generator/review_generator.py`) generates each feedback section and only passes it through `ContentFilter.filter()` (`safety/content_filter.py`), which strips genuinely harmful phrases (self-harm, hate speech, illegal activity) via regex — it has no concept of *tone*. A section can be vague, discouraging, or dismissive and still ship untouched. Done looks like: after generation, each section gets classified constructive vs. not (e.g. via an LLM-as-judge prompt); sections that fail get rejected and regenerated before reaching the user, so nothing dismissive or vague ever shows up in a review. Confirmed both referenced files exist and read them in full — `content_filter.py` (42 lines) and `review_generator.py` (208 lines).

*Part 2 — Tier fit.* Tier 2, per the issue's `tier-2` label — confirmed this requires touching two modules (safety layer + generation pipeline), not a single-file fix. I have prior experience working in large, production codebases through my SRE role, so a Tier 2 scope is a reasonable stretch rather than a blind leap.

*Part 3 — Codebase readiness.* Read `ContentFilter.filter()` end-to-end — a static method returning `(filtered_text, was_filtered)`, pattern-based, no LLM call. Read `ReviewGenerator.generate_section()` and `generate_full_review()` — the per-section loop in `generate_full_review()` (around the `_add_citations` call) is the natural hook point for a post-generation tone check, with a retry/regenerate path back through `generate_section()` for failing sections. No test file exists yet for either module's tone behavior (`tests/unit/test_content_filter.py` doesn't exist) — I'll be writing it from scratch. Read `tests/unit/test_bias_detector.py` end-to-end as the closest existing pattern: pytest, `@pytest.mark.unit`, class-based suite, simple assertions on a `(bool, reason)` return tuple — a solid template for a tone-classification test.

*Part 4 — Scope and time.* Checked issue comments: I claimed it 2026-07-15; two other students (`Jordy-03`, `Shubham91999`) have also commented, one with a similar ToneChecker/LLM-as-judge plan. Per the cohort ledger, both are in other cohorts, so within my own cohort I'm not competing for coaching or peer review on this issue — claims are non-exclusive regardless, so I'm fine working alongside them either way. Confirmed via the GitHub API there are no open blockers or unresolved dependencies on this issue. Time estimate: Tier 2 issues run 8–12 hours; given my SRE job, coursework, and family schedule, this is tight but doable — I'll need dedicated deep-work blocks across weeks 8–9 rather than picking it up in scraps of spare time.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/linneacastro/pathreview/commit/9b6dc554684b9ba5855b473b436040a686464ca8

**Reproduction summary:**
Fed dismissive/discouraging (but not overtly harmful) feedback text directly into `ContentFilter.filter()` and into a mocked `ReviewGenerator.generate_section()` LLM response — both passed the text through completely unchanged, confirming neither module performs any tone classification. Captured as a failing test in `tests/unit/test_content_filter.py` that currently fails (`assert False is True`) because no tone check exists yet.

**PLAN.md link:** https://github.com/linneacastro/pathreview/blob/feat/69-feedback-tone-check/PLAN.md

**Walkthrough video (recommended):** not recorded (optional field)

**Blockers or open questions:**
Whether wiring the fix into the live pipeline is in scope for #69. Traced every caller of `ReviewGenerator`/`ContentFilter` (`grep` across the whole repo) and found neither is invoked anywhere outside their own files — the real API path (`POST /reviews` → `process_review()` in `core/services/review_service.py`) is entirely stubbed: `_run_rag_retrieval_generation()` returns hardcoded canned text, and `_run_safety_checks()` — whose own docstring says it should "validate feedback tone and constructiveness" — only checks structural completeness, never tone. So even a correct fix to the two files the issue names wouldn't be exercised by the running app today. Plan to confirm with a TA/on Slack before Week 9 whether that wiring is part of this issue or a separate one.

**Reproduction steps (detail):**
1. Fed a clearly dismissive/discouraging (but not "harmful") piece of feedback text directly into `ContentFilter.filter()`. Result: `was_filtered=False`, text returned byte-for-byte unchanged. It only regex-matches specific harmful patterns (self-harm, hate speech, illegal activity) — dismissive tone isn't one of them.
2. Mocked the OpenAI client inside `ReviewGenerator` (no API key needed — confirmed `.env` has no `OPENROUTER_API_KEY` set) to return that same discouraging text as if it were real LLM output, then called `generate_section()`. Result: the returned `FeedbackSection.content` was identical to the raw mocked LLM output — `generate_section()` goes straight from LLM response to `parse_review_output()` with no classification step in between.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Ahead of schedule as of Monday 2026-08-03 — all 5 sub-tasks from PLAN.md are implemented and committed on `feat/69-feedback-tone-check`:
1. Design decision: surveyed the existing safety/evaluator checkers (`ContentFilter`, `BiasDetector`, `FaithfulnessChecker`) and found all three are heuristic-only, no real LLM call — followed that precedent instead of PLAN.md's original LLM-as-judge sketch. Recorded in PLAN.md.
2. `ContentFilter.filter()` extended with `DISCOURAGING_PATTERNS` — flags discouraging tone (without redacting it in place, unlike harmful content). Fixes the Week 8 reproduction test (`test_discouraging_feedback_is_flagged`), now passing.
3. New `ToneChecker` class (`safety/tone_checker.py`) — heuristic classifier combining a minimum-length check, generic-praise/vagueness patterns, and reuse of `ContentFilter` for discouraging-language detection.
4. `ReviewGenerator.generate_section()` gated by `ToneChecker` with a bounded regenerate-on-fail loop (max 2 retries, 3 total generation attempts) before falling back to a safe placeholder section.
5. Found and fixed one incidental pre-existing bug (dead unused variable in `output_parser.py`, blocking the local mypy pre-commit hook transitively) — committed separately from the tone-check work since it's unrelated to #69.

27 new tests added across `tests/unit/test_content_filter.py` (+8), `tests/unit/test_tone_checker.py` (new, 14), `tests/unit/test_review_generator.py` (new, 5). Verified against a clean baseline (git worktree at the pre-Week-9 commit): `make test-unit` went from 54 failed/375 passed to 53 failed/403 passed — zero regressions, target test now passes. `make check` numbers also only improved (ruff 182→176 errors, black 52→49 files needing reformat, mypy unchanged at 5 pre-existing errors in 4 files — missing type stubs and a numpy/mypy version conflict, all environment issues unrelated to this change).

**Next steps:**
Push the 5 commits to my fork and open the PR — not done yet as of this check-in.

**Blockers:**
None blocking. The open scope question (whether wiring into `core/services/review_service.py`'s live pipeline belongs in #69) still has no TA/Slack answer — proceeding with the safe default of leaving it out of scope, per the decision recorded in PLAN.md, rather than waiting on it. Skipping the optional draft-PR peer review step this week due to time constraints.

---

### Check-in 2 (end of week)

**Due:** originally Sun 2026-08-02; submitted Mon 2026-08-03, within the 2-day grace period.

**PR link:** https://github.com/ascherj/pathreview/pull/743

**Branch:** `feat/69-feedback-tone-check`

**What you built:**
Added a tone check to the feedback-generation pipeline so discouraging or vague sections no longer ship to users unchanged. `ContentFilter.filter()` now flags discouraging tone via a new `DISCOURAGING_PATTERNS` list; a new `ToneChecker` class (heuristic — length + vagueness checks plus reuse of `ContentFilter`, matching the no-real-LLM-call pattern already used by `ContentFilter`/`BiasDetector`/`FaithfulnessChecker`) classifies each generated section; `ReviewGenerator.generate_section()` gates on it, regenerating up to 2 times before falling back to a safe placeholder rather than looping forever.

**Tests added or updated:**
27 new tests: `tests/unit/test_content_filter.py` (+8, covers the discouraging patterns, harsh-but-fair edge case, empty input), `tests/unit/test_tone_checker.py` (new, 14, covers vagueness/length/discouraging classification), `tests/unit/test_review_generator.py` (new, 5, mocks the OpenAI client to cover constructive-first-try, discouraging-then-regenerate, vague-then-regenerate, and exhausted-retries-returns-fallback).

**Self-review confirmation:** [x] make check passes (no new failures vs. baseline — ruff 182→176, black 52→49 files, mypy unchanged at 5 pre-existing errors)  [x] make test-unit passes (no new failures vs. baseline — 54→53 failed, 375→403 passed)

**Draft PR feedback received from:** none (peer review step skipped this week — time constraints)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No review has come in yet.

**How you responded:**


---

### Reflection

**What was harder than you expected?**
Harder than expected was not the code. It was finding out that an assumption I made about how the system worked was wrong. I assumed that fixing ContentFilter and ReviewGenerator, the two files the issue named, would actually change what users see. Before writing any code, I traced every caller of both classes across the repo. Neither class is used anywhere outside its own file. The real API path, from POST /reviews through process_review() to _run_safety_checks(), is completely stubbed. The docstring for _run_safety_checks() says it should validate feedback tone and constructiveness, but it only checks that fields are not empty. So a correct, fully tested fix to the two named files would not actually reach a real user, because the live pipeline never calls either class. I had to manage that assumption before I could plan the fix.

**What did you learn about working in a large codebase?**
Working in a large codebase taught me how important it is to keep scope tight. I had to stick to the issue I was assigned instead of fixing every other problem I found along the way. I found pre-existing bugs and dozens of unrelated test failures across the repo, and I left them alone, because I did not know what effect a fix might have on other parts of the system I was not familiar with. The one exception was a single unused variable that was blocking my own commit, and even then I confirmed it was safe before touching it.

I also learned that you have to understand how a codebase already works before you start building in it. You have to follow the existing design and logic instead of building it the way you would if it were your own project. For example, every existing safety and evaluation class in this codebase used simple pattern matching instead of calling an LLM, even in a case where an LLM would have been the obvious choice. My original plan was to build a tone checker that called an LLM. I changed the plan to match the existing pattern instead. I was working inside someone else's structure, not designing my own.

**How did AI tools help — and where did they fall short?**
AI helped most with the mechanical work. It moved fast on writing the regex patterns, building 27 tests across three files that matched the existing pytest conventions, and running baseline comparisons through a git worktree to separate pre-existing failures from real regressions. It also caught a documentation problem I would have missed. The CONTRIBUTING.md testing guide claims the repo uses pytest-mock, but that package is not even installed. It matched the actual convention used in the codebase instead.

Where it fell short was anything outside the code itself. It did not know my course deadlines, grace periods, or policies. I had to correct its assumption about when my second check-in was actually due. It also made a mistake in my first PR draft. It reworded the template's testing checkboxes into its own summary instead of keeping the literal checkboxes intact. It caught that mistake itself later, but I would have needed to catch it if I had not been reading closely, since the assignment requires the PR template to be fully filled in as written.

**What would you do differently if you started over?**
If I started over, I would go slower. I would spend more time understanding the codebase as a whole before picking a solution. I did not know how long the issue would actually take to solve, so I jumped to the first solution instead of taking the time to explore the code more first. Next time I would spend more time learning the features and structure of the codebase before starting. I think that kind of understanding also comes from working on more issues in the same codebase over time.

**What are you most proud of from this module?**
What I am most proud of is that this assignment was open-ended in a way the other modules were not. It was not as neatly completable. I had to make decisions and justify them myself instead of being told what to do. The clearest example was deciding not to touch the stubbed parts of the API, like _run_rag_retrieval_generation and _run_safety_checks, even though I could see they were incomplete. I chose to isolate my issue instead of expanding the scope to fix them. Finishing the assignment under those conditions, without someone telling me what the right decision was, felt like a realistic and collaborative way to end the course.
