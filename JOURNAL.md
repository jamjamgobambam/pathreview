## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
[In 3–5 sentences, in your own words: what the issue is (not a copy-paste of
the title), what is currently broken or missing, and what a successful fix
would accomplish. Naming the part of the codebase it affects is helpful context.]

`test_readme_with_all_quality_signals` asserts that fixture README word count is more than 100. However the actual fixture README contains 51 words so the correct scorer behavior fails the test. Extending the fixture word count or modifying the assertion would fix this issue.

**Branch name:** fix/156-readme-scorer-test-fixture-too-short

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/thetireddude/ai201-week7-pathreview/commit/8d8dae87b67def84346d94fe3217b9eb2684d94a

**Reproduction summary:**
[1–2 sentences: How did you reproduce the issue? What did you observe?]

the issue is a failing test case: `test_readme_with_all_quality_signals`. As per the issue description, running `pytest tests/unit/test_readme_scorer.py -q` reproduces the issue. It is observed that the test case fails due to an `assert data["word_count"] > 100` error.

Failing test terminal output:

```python
tests\unit\test_readme_scorer.py F......................         [100%]

============================== FAILURES ===============================
________ TestReadmeScorer.test_readme_with_all_quality_signals ________

self = <tests.unit.test_readme_scorer.TestReadmeScorer object at 0x0000013DF91D0410>
scorer = <agent.tools.readme_scorer.ReadmeScorer object at 0x0000013DF91BCC20>

    def test_readme_with_all_quality_signals(self, scorer):
        """Test README with all quality signals returns high score."""
        readme = """
        # Project Name
        A comprehensive project description.
    
        ## Installation
        ```bash
        pip install package
        ```
    
        ## Usage
        ```python
        import package
        package.run()
        ```
    
        ## Features
        - Feature 1
        - Feature 2
        - Feature 3
    
        ## Tech Stack
        - Python 3.9
        - FastAPI
        - PostgreSQL
    
        ![Build Status](https://example.com/badge.svg)
        ![Coverage](https://example.com/coverage.svg)
    
        ## Live Demo
        [Try it here](https://demo.example.com)
        """
    
        result = scorer.execute({"readme_content": readme})
    
        assert result.success is True
        data = result.data
        assert data["has_readme"] is True
>       assert data["word_count"] > 100
E       assert 51 > 100

tests\unit\test_readme_scorer.py:56: AssertionError
------------------------ Captured stdout call -------------------------
2026-08-05 10:55:53 [info     ] readme_scored                  category=minimal score=0.8717142857142858 word_count=51
======================= short test summary info =======================
FAILED tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals - assert 51 > 100
==================== 1 failed, 22 passed in 0.82s =====================
```

**PLAN.md link:** [PLAN.md](./PLAN.md)

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
[Anything you're still uncertain about going into Week 9, or leave blank]