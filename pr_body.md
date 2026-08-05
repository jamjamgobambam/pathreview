Summary:
Avoid loading persisted agent session state by default. The orchestrator now starts a fresh session for each run unless callers explicitly set profile_data["resume"] to true.

Issue:
Closes https://github.com/ascherj/pathreview/issues/43

Changes:
- agent/orchestrator.py: Only load persisted session state when `profile_data["resume"]` is truthy.
- tests/unit/test_orchestrator_session.py: Added test to ensure fresh runs do not retain stale session data.
- JOURNAL.md: Week 9 check-ins added.

Testing:
- Ran the new unit test locally inside .venv; it passed.
- Ran `make check` and `make test-unit` before and after the change and confirmed no new failures were introduced. The repo contains other pre-existing lint/type/test issues (documented in Check-in 2) that are outside this fix's scope.

Notes for reviewers:
- This change narrows session persistence behavior to avoid surprising state leakage. Reviewers should verify a new review run for the same profile_id produces fresh results when `resume` is not set.
- To manually verify locally:
  1. Start with a profile that has a seeded/stale session in the session store.
  2. Run the orchestrator without `resume` set — verify fresh too  2esults replace the persisted entries.
  3. Run again with `profile_data['resume']=True` — verify previous session state is loaded.
