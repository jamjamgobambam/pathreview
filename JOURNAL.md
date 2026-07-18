# PathReview Contribution Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/71

**Issue title:** Implement a red-teaming test suite for the prompt injection defense

**Tier:** [ ] Tier 1  [ ] Tier 2  [x] Tier 3

**Problem summary:**
PathReview’s safety layer (`safety/prompt_defense.py`) detects and sanitizes prompt injection attempts, but there is no automated red-team suite that proves known attacks are blocked. Without `tests/security/test_prompt_injection.py` and a fixture corpus under `tests/fixtures/injection_attempts/`, regressions in `PromptDefense` can slip into PRs that touch `safety/`. A successful fix adds a curated set of injection payloads, asserts every attempt is detected/blocked, and wires the suite so CI runs it whenever safety code changes.

**Branch name:** `test/71-prompt-injection-red-team`

**Branch URL (submit this):** https://github.com/Anush-Prabhu/pathreview/tree/test/71-prompt-injection-red-team

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [ ] Issue added to cohort ledger *(Section 2B tab → Anush / Anush-Prabhu / #71)*

### "Is this right for me?" — selection notes

- **Scope is Tier 3 (7–10 hours):** Bigger than a Tier 1 fixture fix — building a fixture corpus + security tests + CI gating for `safety/`. Acceptable because Module 3 encourages stretching into harder tiers once setup is done.
- **Clear acceptance criteria:** Issue names exact paths (`tests/security/test_prompt_injection.py`, `tests/fixtures/injection_attempts/`) and the success condition (all curated attacks blocked; run on PRs touching `safety/`).
- **Touches a bounded subsystem:** Concentrated in `safety/prompt_defense.py` and new test/fixture files — good learning surface for the safety layer without rewriting the whole agent/RAG stack.
- **Skills match:** Comfortable writing pytest suites and reading regex-based defense code; local app already runs so I can iterate on failing cases quickly.
- **Why this over a Tier 1:** I want deeper practice on AI safety (prompt injection), which is core to PathReview’s product risk. Claim thread on #71 is still relatively light vs. popular Tier 1 bugs.

### Progress this week

- Forked `ascherj/pathreview` → `Anush-Prabhu/pathreview`, added `upstream` remote.
- Confirmed app loads at http://localhost:5173 (`make run` with Docker services up).
- Selected and claimed [#71](https://github.com/ascherj/pathreview/issues/71) (Section 2B).
- Opened working branch `test/71-prompt-injection-red-team` with this journal.
