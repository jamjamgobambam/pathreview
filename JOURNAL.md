# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** [Issue #119 — Add inline docstrings to all public methods in `core/services/`](https://github.com/ascherj/pathreview/issues/119)

**Issue title:** Add inline docstrings to all public methods in `core/services/`

**Tier:** [ ] Tier 1  [x] Tier 2  [ ] Tier 3

**Problem summary:**
The public service functions in `core/services/` have only brief descriptions instead of complete Google-style docstrings. Their parameters, return values, and possible exceptions are therefore not documented for contributors or generated API documentation. The current checkout contains public functions in `profile_service.py` and `review_service.py`; the `notification_service.py` named in the issue does not currently exist, so creating a new service would be outside this documentation-only scope. A successful contribution will document every existing public service function with accurate descriptions and applicable `Args`, `Returns`, and `Raises` sections without changing runtime behavior.

**Selection notes — “Is this right for me?” checklist:**

- [x] I confirmed the issue is open, labeled `tier-2` and `docs`, and already claimed it with a comment from my GitHub account.
- [x] I reviewed the named service modules and identified a bounded documentation-only change across two existing files.
- [x] Tier 2 is a good fit for my comfort level: the edits are approachable, while accurately documenting database sessions, ownership checks, return types, and exceptions requires understanding several connected models and schemas.
- [x] The expected outcome and validation are clear: preserve behavior, use the repository's required Google-style format, and run the documentation/code-quality checks.
- [x] I accounted for the missing `notification_service.py` and will not expand the task by inventing a new service; I would confirm that interpretation with the maintainer if implementation begins before clarification is posted.

**Branch name:** `docs/119-add-service-docstrings`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to the [AI201 Su26 PathReview Cohort Issue Ledger](https://docs.google.com/spreadsheets/d/1oclK-70-klhGofiaw6krk8-zV_wZiumsR-Xnd_l5ZR8/edit)
