# Journal

## Week 7 — Issue selection

**Issue link:** [#146 — PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` has a `phone_us` regex that already accounts for optional parentheses around the area code, but the separator it expects right after the closing `)` is limited to `-` or `.` — a plain space isn't allowed there. Since the conventional parenthesized format is written as `(555) 123-4567`, with a space after the `)`, the match breaks at exactly that point and the number passes through unredacted. `scrub()` leaves it in the output text, and `detect()` returns an empty list for text that contains only a parenthesized number, which is a real gap in a safety component whose entire job is catching this. A successful fix widens the separator character class (or otherwise permits whitespace there) so both `(555) 123-4567` and `(555)123-4567` are recognized alongside the dashed and dotted formats, and gets the related failing tests passing: `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and `test_phone_at_start_of_text` in `tests/unit/test_pii_scrubber.py`.

**"Is this right for me?" checklist reasoning:**

*Part 1 — Understanding the issue:* Paraphrased without re-reading: the phone regex in the scrubber doesn't allow a space after the closing parenthesis in `(555) 123-4567`, so that common format slips through both `scrub()` and `detect()` unredacted. Affected area: `safety/` (matches the issue's `safety` label). I opened `safety/pii_scrubber.py` and confirmed the `PII_PATTERNS["phone_us"]` regex and both methods that use it (`scrub`, `detect`) exist as described. Before/after: before the fix, `scrub("Call me at (555) 123-4567")` returns the phone number untouched and `detect(...)` returns `[]`; after the fix, both should treat it the same as the dashed format — `scrub` replaces it with `[REDACTED]`, `detect` returns a `phone_us` entry with the right `start`/`end` offsets.

*Part 2 — Tier fit:* Tagged `tier-1` / `good first issue` on the tracker, and this is my first contribution to this codebase, so Tier 1 is the right level — no cross-module or system-wide understanding needed, just this one regex.

*Part 3 — Codebase readiness:* Read the full `phone_us` pattern (not just the file) and traced how it flows through `scrub()` and `detect()`. Read `tests/unit/test_pii_scrubber.py` end-to-end — tests follow a simple `PIIScrubber()` fixture + `scrub`/`detect` call + assertion pattern, with `test_us_phone_formats` looping over a list of format strings, which is exactly where a parenthesized-with-space case belongs. I can already sketch the fix (adjust the separator character class in the regex) without needing to look anything else up.

*Part 4 — Scope and time:* Checked issue #146's comments and found no other explicit claim comments, though PR #162 (open, unmerged, no reviews yet) bundles a fix for #146 in with three other unrelated issues — normal for an open-source tracker where claims aren't exclusive. I'm proceeding with my own independent fix rather than treating it as resolved, and logged my claim in the cohort ledger per the Claims column. Estimated time: 1–2 hours for the regex change plus new/updated tests, well inside the 3–6 hour Tier 1 range and comfortably within the Week 8–9 window. No "blocked by" references or unresolved dependencies on the issue.

**Branch name:** `fix/146-parenthesized-phone-scrub`

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [e7a8280](https://github.com/csharathkumar/pathreview/commit/e7a8280038849d82ebdecb5ebb84fa2bdec34274)

**Reproduction summary:**
Ran `scripts/repro_issue_146.py` against the live `PIIScrubber` class: `scrub("Call me at (555) 123-4567 or 555-123-4567")` redacted the dashed number but left `(555) 123-4567` untouched, and `detect("Call me at (555) 123-4567")` returned `[]` with no phone detected at all. Root cause confirmed in `safety/pii_scrubber.py`: the `phone_us` regex allows `-` or `.` right after the closing `)`, but not a space, and the conventional parenthesized format always has a space there.

**PLAN.md link:** [PLAN.md](https://github.com/csharathkumar/pathreview/blob/fix/146-parenthesized-phone-scrub/PLAN.md)

**Walkthrough video (recommended):** (not recorded)

**Blockers or open questions:**
Still deciding between the smallest possible regex change (widen the separator character class to include whitespace) versus splitting `phone_us` into explicit dashed/dotted vs. parenthesized alternatives for readability. Need to verify the widened pattern doesn't introduce false positives on unrelated space-separated digit groups before committing to the simplest fix — see Risks & Unknowns in `PLAN.md`.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix: replaced the `phone_us` regex's leading `\b` with `(?<!\w)` so a leading `(`/`+` is included in the redacted match, and widened the separator character class from `[-.]?` to `[-.\s]?` so whitespace is accepted. This resolved all 4 originally-failing tests plus a second latent bug I found in the same regex (`+1 555 123 4567` was also failing, for the same root cause). Added 3 new tests (`test_detect_parenthesized_phone_only`, `test_scrub_parenthesized_and_dashed_phone_together`, `test_phone_us_space_separated_tradeoff`) and type-annotated all existing test methods to satisfy the repo's mypy pre-commit hook. Along the way, fixed several pre-existing lint issues confined to the two files I'm editing, and confirmed (via `git stash` before/after comparison) that one remaining test failure (`test_mixed_pii_and_text`) is a pre-existing, unrelated bug in the `street_address` pattern, not something I introduced. Pushed the fix and opened a draft PR (#491).

**Next steps:**
Fill in the PR description (currently just the empty template), get peer/mentor review in Slack, address any feedback, then mark the PR ready for review before Sunday's deadline.

**Blockers:**
None currently. Earlier hiccups (zsh mangling a commit message containing `!`, and `make format` reformatting 51 unrelated files repo-wide) are resolved — commits are clean and scoped to just the 4 relevant files.

---

### Check-in 2 (end of week)

**PR link:** [#491 — fix(safety): redact parenthesized and space-separated US phone numbers](https://github.com/ascherj/pathreview/pull/491)

**Branch:** `fix/146-parenthesized-phone-scrub`

**What you built:**
Fixed the `phone_us` regex in `safety/pii_scrubber.py` so `scrub()`/`detect()` correctly catch parenthesized US phone numbers like `(555) 123-4567`, plus a second latent gap I found in the same pattern affecting space-separated numbers like `+1 555 123 4567`. The fix replaces the leading `\b` with `(?<!\w)` (so a leading `(`/`+` is included in the redacted match instead of left behind) and widens the separator character class to accept whitespace alongside `-`/`.`.

**Tests added or updated:**
`tests/unit/test_pii_scrubber.py` — added `test_detect_parenthesized_phone_only`, `test_scrub_parenthesized_and_dashed_phone_together`, and `test_phone_us_space_separated_tradeoff` (documents the accepted over-redaction trade-off from widening the separator class). Also added type annotations to all 29 existing test methods to satisfy the repo's mypy pre-commit hook.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(Scoped to the 4 files this PR touches: `ruff`, `black --check`, and `mypy` all clean; `pytest tests/unit/test_pii_scrubber.py` is 27 passed / 1 failed. The 1 failure, `test_mixed_pii_and_text`, is a pre-existing bug in the unrelated `street_address` pattern — confirmed via `git stash` comparison that it fails identically on `main`, before this PR's changes. Per this week's guidance on pre-existing failures, "passes" here means no new failures were introduced; documented in the PR's "Notes for Reviewers" along with ~159 pre-existing repo-wide `ruff` errors and other pre-existing `make test-unit` failures in unrelated modules.)

**Draft PR feedback received from:** Posted in the cohort Slack channel asking for review; no response yet as of submission. PR was moved from draft to ready-for-review regardless, per this week's guidance that peer review is encouraged but "none" is an acceptable answer here.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer comments came in on PR #491 by the end of the module (confirmed by checking the PR: "No reviews", 1 participant). Per the Su26 note, reviewer feedback isn't a feature this term, so this was expected. I did post the PR in the cohort Slack channel in Week 9 asking for a peer look, but got no response there either.

**How you responded:**
N/A — no feedback arrived to respond to.

---

### Reflection

**What was harder than you expected?**
Environment setup ate more time than I expected before I'd written a single line related to the actual bug — a Python version mismatch (system Python was 3.9, project needed 3.11+), Docker not being installed at all, and then a non-obvious port mismatch (Postgres mapped to 5433, not 5432, and nothing worked until `.env` was copied from `.env.example`). None of that was about the issue itself, but it all had to be solved first. Later in the process, the tooling itself became the obstacle: the repo's pre-commit mypy hook checks `tests/` even though the `Makefile`'s own `make typecheck` target explicitly excludes it, so my commit kept failing locally with 29 "missing type annotation" errors on test methods I hadn't written, until I annotated the entire file. I also learned the hard way that `make format` runs `black` against the *whole repo*, not just my files — it silently reformatted 51 unrelated files, and if I hadn't checked `git status` carefully I'd have shipped a PR with a repo-wide diff that had nothing to do with issue #146.

**What did you learn about working in a large codebase?**
The single biggest shift was learning to prove, not assume, whether a failure is mine. When `test_mixed_pii_and_text` started failing after my regex change, my first instinct was that I'd broken something. Instead of guessing, I used `git stash` to run the exact same test against the pre-fix code and confirmed it was already broken (a separate bug in the `street_address` pattern). That habit — isolate, compare against a clean baseline, then decide — is not something I'd needed as much building things from scratch, where if a test fails, it's almost always because of the thing I just wrote. In someone else's large codebase, that assumption doesn't hold, and there's a lot of debt that's simply not yours to fix (the repo had ~159 pre-existing lint errors and dozens of pre-existing failing tests across totally unrelated modules). Also learned that even a single well-scoped Tier 1 issue touches more surface area than it first appears — the actual root cause (a missing `\s` in a character class, and a `\b` that couldn't fire before an unconsumed `(`) was two lines of diff, but understanding *why* it failed, and confirming it didn't quietly break something else, took far more investigation than the fix itself.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for fast, disposable experimentation: before touching the real `pii_scrubber.py`, I could test candidate regex patterns against a dozen edge cases (parens with/without spaces, `+1` prefixes, false-positive risks like "order 123 456 7890") in seconds, which is what let me catch the over-redaction trade-off and the leading-paren cosmetic bug before they became review comments. It also helped systematically distinguish pre-existing failures from ones I introduced, and kept the PR description, `PLAN.md`, and journal entries consistent with what actually happened rather than what I remembered happening. Where it fell short: it initially suggested running the full `make format`/`make check` without flagging that these are repo-wide commands, which caused the 51-file reformatting scare — a mistake I had to catch by reading `git status` closely, not something the tool caught proactively. It also couldn't run anything in my actual project environment (no network access to install dependencies, couldn't commit through git due to sandbox restrictions), so every actual verification — `make check`, `make test-unit`, the real commit and push — still had to happen in my own terminal. AI was a fast way to reason about *what* to check; it wasn't a substitute for actually running it myself.

**What would you do differently if you started over?**
I'd run the *scoped* lint/format/typecheck commands (just the files I'm touching) from the very first check, rather than reaching for the full `make check`/`make format` targets and then having to untangle an unrelated 51-file diff afterward. I'd also establish the "before" baseline explicitly and early — run `make check` and `make test-unit` on a clean checkout *before* writing any fix, the way this module's instructions actually recommended — instead of discovering the pre-existing failures reactively partway through, which meant redoing some verification work. I'd also spend a bit more time up front reading PR #162 (another contributor's bundled fix that included this same issue) before finalizing my own approach, just to sanity-check whether there was a simpler fix I was missing — I looked at it but didn't dig in as deeply as I could have.

**What are you most proud of from this module?**
Catching that the issue as written was incomplete. The ticket said the bug was about parenthesized numbers, but while testing the fix I found that `+1 555 123 4567` — a completely different format, with no parentheses at all — was *also* silently failing against the original regex, for a related but distinct reason (whitespace wasn't accepted as a separator anywhere in the pattern, not just after the closing paren). That wasn't mentioned anywhere in the issue. Finding it took actually running the regex against every format in the test file rather than trusting the issue's framing, and it meant the fix I shipped actually closed both gaps instead of leaving a documented "known issue" behind for the next person.
