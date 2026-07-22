# Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/156

**Issue title:** README scorer test fixture is too short for its own word-count assertion

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The unit test `test_readme_with_all_quality_signals` in
`tests/unit/test_readme_scorer.py` is supposed to prove that a rich,
well-structured README earns a high quality score. It asserts
`word_count > 100` and `word_count_category == "comprehensive"`. The problem is
the README string used as the test fixture only contains about 51 words, so
those two assertions fail — not because the scorer is wrong, but because the
fixture is too small to reach the thresholds. The scoring logic in
`agent/tools/readme_scorer.py` counts words with `content.split()` and labels
anything under 100 words as `minimal` and anything with 500+ words as
`comprehensive`, so 51 words is correctly categorized as `minimal`. A
successful fix extends the fixture README with enough genuine content (500+
words) so the test actually exercises the `comprehensive` branch it claims to
test, making the assertions pass against correct scorer behavior.

**Branch name:** fix/156-readme-scorer-word-count-fixture

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger

---

### "Is this right for me?" checklist — scope reasoning

- **Single, well-defined file.** The change is contained to the test module
  `tests/unit/test_readme_scorer.py` (and possibly a fixture file). No
  production code in `agent/tools/readme_scorer.py` needs to change.
- **Reproducible failure.** `pytest tests/unit/test_readme_scorer.py -q` fails
  today with `assert 51 > 100`, so I have a clear before/after signal.
- **Low blast radius.** Extending a test fixture can't break runtime behavior;
  the risk is limited to the test suite.
- **Right size for a first contribution.** Matches the Tier 1 "good first
  issue" profile — small, understandable, and verifiable end-to-end.
