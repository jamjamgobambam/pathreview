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

## Week 8 — Reproduction

Traced actual callers of the issue's two named modules (`grep` across the whole repo) and confirmed neither `ReviewGenerator` nor `ContentFilter` is invoked anywhere outside their own files — the live API path (`POST /reviews` → `process_review()` in `core/services/review_service.py`) is entirely stubbed: `_run_rag_retrieval_generation()` returns hardcoded canned text, and `_run_safety_checks()` — whose own docstring says it should "validate feedback tone and constructiveness" — only checks structural completeness (non-empty fields, confidence in `[0,1]`), never tone. So triggering a review through the running app wouldn't exercise real generation at all today. Reproduced at the module level instead, matching the issue's own "relevant files" list.

**Reproduction steps:**
1. Fed a clearly dismissive/discouraging (but not "harmful") piece of feedback text directly into `ContentFilter.filter()`. Result: `was_filtered=False`, text returned byte-for-byte unchanged. It only regex-matches specific harmful patterns (self-harm, hate speech, illegal activity) — dismissive tone isn't one of them.
2. Mocked the OpenAI client inside `ReviewGenerator` (no API key needed — confirmed `.env` has no `OPENROUTER_API_KEY` set) to return that same discouraging text as if it were real LLM output, then called `generate_section()`. Result: the returned `FeedbackSection.content` was identical to the raw mocked LLM output — `generate_section()` goes straight from LLM response to `parse_review_output()` with no classification step in between.

Committed as a failing test: `tests/unit/test_content_filter.py::TestContentFilterToneCheck::test_discouraging_feedback_is_flagged` — asserts `ContentFilter.filter()` should flag discouraging feedback the same way it flags harmful content. Currently fails (`assert False is True`), confirming the gap; should flip to passing once tone classification is implemented.

**Scope note for Week 9:** the wiring between `review_service.py` and `ReviewGenerator`/`ContentFilter` may not exist yet, or may be intentionally out of scope for #69 — worth confirming with a TA/on Slack before assuming the fix only touches the two named files.
