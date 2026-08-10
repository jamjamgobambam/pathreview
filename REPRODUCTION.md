# Week 8 reproduction notes

## Issue

Issue #156 — README scorer test fixture is too short for its own word-count assertion

Issue link: https://github.com/ascherj/pathreview/issues/156

## Reproduction command

python -m pytest tests/unit/test_readme_scorer.py -q

## Observed result

The failing test is tests/unit/test_readme_scorer.py::TestReadmeScorer::test_readme_with_all_quality_signals.

The test expects data["word_count"] > 100, but the actual scorer output reports word_count=51 and category=minimal.

This confirms the issue locally: the test fixture is too short for its own word-count and comprehensive-category expectations.
