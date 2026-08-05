## Solution plan

**Issue:** README scorer test fixture is too short for its own word-count assertion
https://github.com/ascherj/pathreview/issues/156

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?

The scorer logic itself is correct — _score_readme() does a plain content.split() word count, and 51 is the accurate word count for the fixture in test_readme_with_all_quality_signals. The bug is in the test fixture, not the implementation: the multi-line triple-quoted string was written to look comprehensive (headings, code blocks, bullet lists, badges) but most of that visual bulk is markdown syntax and short lines, not prose — so it only contains ~51 real words. Expected: a README with every quality signal present (install, usage, badges, demo, tech stack) should also cross the 100-word threshold and be scored "comprehensive", since that's the intent of the test name and its assert data["word_count"] > 100 line versus Actual: the fixture asserts word_count > 100 but only contains 51 words, so the test fails against correct scorer behavior.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

Files involved:

* test_readme_scorer.py — test_readme_with_all_quality_signals fixture (primary fix location)
* agent/tools/readme_scorer.py — _score_readme() (read-only reference; confirm no change needed here)

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. Expand the readme string in test_readme_with_all_quality_signals with additional descriptive prose (e.g. longer project description, feature explanations) while preserving all existing structural markers (## Installation, ## Usage, badges, ## Tech Stack, demo link) so every other assertion in the test still holds.
2. Re-run the word count locally against the updated fixture to confirm it exceeds 100 words (targeting comfortably over, e.g. 120–150, to avoid a brittle near-boundary value).
3. Re-verify all other assertions in the same test (has_installation_section, has_usage_section, has_badges, has_demo_link, has_tech_stack_section, overall_score > 0.7) still pass with the expanded content.
4. Scan the rest of test_readme_scorer.py for any other fixtures whose word counts are asserted against a category boundary (e.g. test_word_count_category_adequate, _comprehensive) to confirm they don't have the same mismatch.
5. Run the full test_readme_scorer.py suite to confirm no regressions.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

Input: the existing test fixture string in test_readme_with_all_quality_signals.
Output: a revised fixture string with the same structural markers plus enough additional prose that len(content.split()) > 100, with no changes to readme_scorer.py itself.

### Risks & unknowns
What could go wrong? What are you still unsure about?

* Adding prose could inadvertently introduce new regex matches (e.g. accidentally including the word "install" in a sentence about something unrelated) that change other boolean assertions — needs a careful re-check after editing.
* If the added text pushes word_count just over 500, word_count_category would flip to "comprehensive" category-wise but that's already the intended category per the test name, so this is fine, but worth confirming intentionally rather than by accident.
* Unsure whether other tests in the suite (or elsewhere in the codebase, e.g. any other test file referencing README fixtures) share a copy of this same string — worth a repo-wide search before assuming this is fully isolated.

### Edge cases
What inputs or states should your fix handle gracefully?

* Ensure the expanded fixture still parses cleanly as a Python triple-quoted string (no unescaped backticks/quotes breaking the literal).
* Ensure indentation added for readability doesn't get counted oddly by .split() (it won't, since .split() collapses whitespace, but worth a sanity check).
* Confirm the fixture change doesn't push overall_score to exactly 1.0 or another edge value that could mask future regressions in the scoring formula.