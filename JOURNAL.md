## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1 [ ] Tier 2 [ ] Tier 3

**Problem summary:**
The `PIIScrubber` class in `safety/pii_scrubber.py` contains a regex pattern for US phone numbers that uses `\b` (word boundary) as a leading anchor. Because `\b` only matches at the boundary between a word character (letter or digit) and a non-word character, it cannot anchor before a `(` in formats like `(555) 555-1234` — the opening parenthesis is itself a non-word character, so no word boundary exists there. Additionally, the separator group `[-.]?` between digit clusters does not allow for a space, meaning the common `(555) 555-1234` format (paren, space, digits) will never match. The fix involves relaxing the leading anchor and widening the separator to include spaces, then adding test cases that cover the parenthesized format in `tests/unit/test_pii_scrubber.py`.

**Branch name:** fix/146-pii-scrubber-parenthesized-phones

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/alabhya-ai/pathreview/commit/a16077c05c6b2fd97c2e681634c99a8d95ae31fa

**Reproduction summary:**
I added four targeted failing tests to `tests/unit/test_pii_scrubber.py` covering parenthesized formats: `(555) 555-1234` mid-sentence, at the start of a string, without a space after the closing paren, and with a `+1` country code prefix. All four tests fail against the current regex, confirming the bug is reproducible and precisely located at the `phone_us` pattern in `safety/pii_scrubber.py` line 15.

**PLAN.md link:** [https://github.com/alabhya-ai/pathreview/blob/fix/146-pii-scrubber-parenthesized-phones/PLAN.md](https://github.com/alabhya-ai/pathreview/blob/fix/146-pii-scrubber-parenthesized-phones/PLAN.md)

**Walkthrough video (recommended):** N/A

**Blockers or open questions:**
Need to confirm the Python 3.11 environment is stable before running the full test suite to verify no regressions after the regex fix.

---

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
All sub-tasks from PLAN.md are complete. Applied the one-line regex fix to `safety/pii_scrubber.py`: replaced the leading `\b` with `(?<!\d)`, the trailing `\b` with `(?!\d)`, and widened the area-code-to-exchange separator from `[-.]?` to `[-.\s]?` (and the country-code separator likewise). All 4 reproduction tests now pass. Confirmed no new test failures were introduced.

**Next steps:**
Open the PR, fill in the template, and mark it ready for review.

**Blockers:**
The project's venv runs Python 3.7 which cannot import the codebase (Python 3.9+ type hints cause `TypeError`). Ran the pii_scrubber tests directly with the system Python 3.13 instead. `make test-unit` fails for 18 other test files due to this pre-existing environment issue — documented in Check-in 2.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/422

**Branch:** `fix/146-pii-scrubber-parenthesized-phones`

**What you built:**
Fixed the `phone_us` regex in `PIIScrubber.PII_PATTERNS` (`safety/pii_scrubber.py:15`) so it correctly redacts parenthesized US phone numbers like `(555) 555-1234`. The leading `\b` anchor was replaced with `(?<!\d)` (allowing `(` to precede the match), the trailing `\b` with `(?!\d)`, and the separator between the area code and exchange was widened to `[-.\s]?` so the space after `)` is accepted.

**Tests added or updated:**
`tests/unit/test_pii_scrubber.py` — 4 reproduction tests added in Week 8 (`test_parenthesized_phone_mid_sentence`, `test_parenthesized_phone_start_of_text`, `test_parenthesized_phone_no_space_after_paren`, `test_parenthesized_phone_with_country_code`). All 4 now pass.

**Self-review confirmation:** [ ] make check passes [x] make test-unit passes (pii_scrubber tests pass; pre-existing failures documented below)

**Pre-existing failures in `make test-unit`:**
`make test-unit` exits with code 2 due to 18 collection errors in unrelated test files. All errors are caused by the project venv running Python 3.7, which cannot parse Python 3.9+ generic type hints (`list[dict]`, `str | None`) used throughout the codebase. These failures exist on `main` before any of my changes. My changes introduce no new failures — `test_pii_scrubber.py` (the only file I touched) has 2 failures that are also pre-existing: `test_us_phone_formats` (the `+1 555 123 4567` all-space format was never supported — my fix actually improves this from 2 failing formats to 1) and `test_mixed_pii_and_text` (caused by the unrelated `street_address` regex greedily matching `"5 years developing Python appl"` via the `Pl` suffix keyword).

**Draft PR feedback received from:** none

---

## Week 10 — Reflection

**What was harder than you expected?**
Making sense of the existing test suite was harder than I anticipated. The tests weren't well-documented and several were failing for pre-existing, unrelated reasons (the Python 3.7 venv issue), so it took time to distinguish failures I owned from failures that were already there before I touched anything. Figuring out which failures to care about and which to document-and-ignore was a judgment call I hadn't expected to have to make.

**What did you learn about working in a large codebase?**
Commit message quality matters much more than I expected. In my own projects I write terse commit messages because I'm the only one who reads them — but in a shared repo, good formatting and clear scope (`fix:`, `docs:`, `test:` prefixes, precise subject lines) is how reviewers and future contributors build trust in your changes without reading every line of code. It's a form of communication, not just bookkeeping.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for navigating an unfamiliar codebase quickly — finding the right file, understanding what a regex was doing, and drafting test cases. Where it fell short was around environment and infrastructure issues: when Docker wasn't behaving or environment variables weren't threading through correctly, the AI gave plausible-sounding suggestions that didn't account for the specific state of my local machine. Those problems required me to read logs carefully and reason through the system myself.

**What would you do differently if you started over?**
I'd verify the local environment (venv Python version, `make` targets, Docker) before writing a single line of code. The pre-existing Python 3.7/3.9+ incompatibility cost me time I could have spent on the actual fix, and I only discovered it late because I assumed the environment was healthy.

**What are you most proud of from this module?**
Working with git confidently. By the end I was comfortable branching, staging selectively, writing structured commit messages, and reasoning about what should and shouldn't go into a commit — skills that felt mechanical before but now feel like a natural part of how I think about a change.
