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

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Anush-Prabhu/pathreview/commit/b1365185e5f3e0397fa650c3661429a6caa4769b

**Reproduction summary:**
Added failing `@pytest.mark.security` tests in `tests/security/test_prompt_injection_reproduction.py`. Running them shows the #71 gap clearly: `tests/fixtures/injection_attempts/` and `tests/security/test_prompt_injection.py` are missing, and five curated payloads (`dan_jailbreak`, `base64_instruction`, `translate_then_ignore`, `developer_mode`, `xml_tag_injection`) are not blocked by `PromptDefense.is_injection_attempt` (7 failed assertions total).

**PLAN.md link:** https://github.com/Anush-Prabhu/pathreview/blob/test/71-prompt-injection-red-team/PLAN.md

**Walkthrough video (recommended):** [optional — add Loom link ≤ 2 min]

**Blockers or open questions:**
Whether Week 9 should stay regex-only in `PromptDefense` or add light normalization (e.g. strip XML-ish tags / decode trivial Base64) to catch obfuscated jailbreaks without false-positiving normal resume text.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Completed PLAN sub-tasks 1–3 locally: curated `tests/fixtures/injection_attempts/corpus.json`, implemented `tests/security/test_prompt_injection.py`, and extended `PromptDefense.INJECTION_PATTERNS` so previously missed jailbreak / Base64 / developer-mode / XML-tag payloads are blocked. Retired the Week 8 reproduction-only failing tests.

**Next steps:**
Wire CI `test-security` path filter, run unit + security verification, open PR against `ascherj/pathreview`, and fill Check-in 2 with the PR link.

**Blockers:**
None for the core suite. Full-repo `make check` / `make test-unit` still report many pre-existing failures unrelated to `safety/` (documented in the PR).

### Check-in 2 (submission)

**PR link:** https://github.com/ascherj/pathreview/pull/640

**Branch:** `test/71-prompt-injection-red-team`

**What you built:**
Added an automated red-team suite for prompt injection defense: a JSON attack/benign corpus, security-marked pytest coverage that asserts every curated attack is blocked, stronger regex detection in `PromptDefense`, and a CI job that runs `-m security` when `safety/` or the suite/fixtures change.

**Tests added or updated:**
- `tests/security/test_prompt_injection.py` — corpus existence, attack blocked, benign not flagged, sanitize XML tags
- `tests/fixtures/injection_attempts/corpus.json` — 10 attacks + 5 benign controls
- `tests/unit/test_prompt_defense.py` — existing unit tests still pass (no regressions on prior patterns)
- Removed `tests/security/test_prompt_injection_reproduction.py` (Week 8 failing repro)

**Self-review confirmation:**
- [x] `make check` — no new failures in changed files (`ruff`/`black`/`mypy` clean on `safety/prompt_defense.py` + new security tests). Full-repo `make lint` still has pre-existing F841/etc. elsewhere.
- [x] `make test-unit` — no new failures from this change; `tests/unit/test_prompt_defense.py` all pass. Repo-wide unit run still has pre-existing failures in unrelated modules (skill extractor, structural chunker, tech detector, etc.).
- [x] Security suite: `pytest tests/security -m security` → 18 passed

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No – still awaiting review

**Summary of feedback:**
No reviewer comments on [PR #640](https://github.com/ascherj/pathreview/pull/640) as of Week 10. Per Su26 course note, maintainer review is not expected this term, so I’m documenting “no feedback” and closing out the module with reflection.

**How you responded:**
N/A — no review comments to address. Left the PR open and ready for review with the template fully filled in.

### Reflection

**What was harder than you expected?**
Reproducing #71 properly in Week 8. I expected “missing tests” to be enough, but probing `PromptDefense` with real jailbreak payloads showed several attacks already slipped through — so the issue was both a missing suite *and* a weak detector. Getting Docker/WSL working on Windows also ate more setup time than I planned before I could even run the app.

**What did you learn about working in a large codebase?**
You can’t treat PathReview like a greenfield app. Changes have to match existing patterns (`@pytest.mark.security`, CONTRIBUTING branch names, CI layout), and full-repo `make check` / `make test-unit` already fail in unrelated modules — so the bar is “don’t make it worse,” not “fix the whole suite.” Tracing from issue → `safety/prompt_defense.py` → unit tests → CI was more important than rewriting lots of code.

**How did AI tools help — and where did they fall short?**
AI helped navigate the multi-module layout, draft the corpus/tests, and fill PLAN/JOURNAL templates quickly. It fell short on environment reality (WSL/Docker first-run, Windows encoding in seed scripts, pre-commit mypy edge cases) — those needed hands-on debugging. I also had to review every AI-suggested regex so benign resume text like “I learned to ignore flaky tests…” wasn’t falsely flagged.

**What would you do differently if you started over?**
I’d open a draft PR earlier in Week 9 for peer feedback, and I’d pick the Tier 3 issue only after a tighter Week 7 “is this right for me?” pass on effort (7–10 hours). I’d also write the red-team corpus *before* expanding patterns, so every defense change is driven by a failing case instead of guessing regexes first.

**What are you most proud of from this module?**
The end-to-end contribution loop on #71: claim → reproduce with failing security tests → PLAN → real suite + hardened defense + CI path filter → submitted PR. Especially the benign controls in the corpus — they forced me to keep detection specific instead of just blocking anything with the word “ignore.”
