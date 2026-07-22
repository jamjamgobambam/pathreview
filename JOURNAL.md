# Module 3 Journal — Ashraful Islam (AI01010)

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The unit test `test_readme_with_all_quality_signals` in `tests/unit/test_readme_scorer.py` is supposed to verify that the README scorer (part of the agent's tool suite in `agent/tools/readme_scorer.py`) gives high marks to a comprehensive README. However, the sample README hard-coded into the test is only about 50 words long, while the test asserts that the scorer reports a word count above 100 and a "comprehensive" category. The scorer is actually behaving correctly — it is the test fixture that contradicts its own assertions, so the test fails even on correct code. A successful fix expands the fixture README to realistically exceed 100 words (keeping all the quality signals it checks for: installation and usage sections, badges, demo link, tech stack) so the test passes for the right reason and genuinely validates the scorer's behavior.

**Branch name:** fix/156-readme-scorer-test-fixture

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

**"Is this right for me?" checklist reasoning:**
Scope: the change is contained to a single test file (`tests/unit/test_readme_scorer.py`), which matches the Tier 1 definition of "scoped to a single file or config." Reproducibility: the failure is deterministic — running `pytest tests/unit/test_readme_scorer.py -q` shows the failing assertion (`assert 51 > 100`) with no external services, API keys, or Docker dependencies required. Understandability: I can explain the bug end-to-end (fixture contradicts its assertions) without needing to understand the RAG or agent orchestration layers. Risk: no application code changes, so there is no chance of breaking other modules; the definition of done is clear (the test passes against unmodified scorer code). This is my first contribution to a large multi-service codebase, so a well-scoped test fix lets me focus on learning the project's contribution standards (branch naming, Conventional Commits, make check / make test-unit) with room to take on a second, harder issue if I finish early.
