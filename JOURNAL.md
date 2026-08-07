## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Why this tier:** Chose Tier 1 as my first contribution to a large codebase — the fix is contained to one regex in one file with pre-written tests, a realistic scope for a two-week window.

**Problem summary:**
The PII scrubber in `safety/pii_scrubber.py` uses one regex to find phone numbers, but it only allows dashes or dots between digit groups so parenthesized numbers like (555) 123-4567 don't match and slip through un-redacted, with `detect()` reporting no PII. A successful fix widens the pattern to catch parenthesized and space-separated formats without breaking the dashed/dotted ones already handled, making the four failing tests in `tests/unit/test_pii_scrubber.py` pass.

**Branch name:** fix/146-parenthesized-phone-number-error

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/soccerjonj/pathreview/commit/447244e702bc3be4794dcd632922aa98392c274d

**Reproduction summary:**
I ran the pytest `pytest tests/unit/test_pii_scrubber.py -v` and observed 20 passes and 5 failures. The tests that failed were: `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, `test_phone_at_start_of_text`, and lastly a test that surfaced a second bug, `test_mixed_pii_and_text`. Line 15 is where my reported bug occurs. The `phone_us` regex logic currently doesn't work for parenthesized and space-separated numbers. Line 18 is where the second bug I found is. The second bug has to do with the `street_address` regex pattern. This is out of scope for me but noted. 

**PLAN.md link:** https://github.com/soccerjonj/pathreview/blob/fix/146-parenthesized-phone-number-error/PLAN.md

**Blockers or open questions:**
I'm not sure whether the `street_address` false-positive bug I found in `test_mixed_pii_and_text` should get its own GitHub issue filed against upstream, or if noting it here is sufficient for this assignment. I'm also unsure whether reviewers will want the regex to handle repeated/multiple separator characters (e.g. double spaces) or if treating that as out of scope is the right call.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented and committed both sub-tasks from `PLAN.md`: widened the `phone_us` regex in `safety/pii_scrubber.py` to accept a space as a separator (commit `3acc732`), and added a no-space parenthesized edge case (`"(555)123-4567"`) to `test_us_phone_formats` (commit `aad7a64`). All 4 originally-failing phone tests now pass, plus the new edge case. Also, cleaned up four pre-existing lint issues across both touched files (`E501`, `B007` in `pii_scrubber.py`; two `F841`s in `test_pii_scrubber.py`).

**Next steps:**
Run the full `make test-unit` and `make check` suite to confirm no new regressions beyond the documented pre-existing failures, then open the PR against `ascherj/pathreview` following the `CONTRIBUTING.md` template.

**Blockers:**
One open judgment call, carried from Week 8: whether the `street_address` false-positive bug (`test_mixed_pii_and_text`) needs its own filed issue. Also had to skip the `mypy` pre-commit hook (`SKIP=mypy`) for the test-file commit since all 409 test functions repo-wide lack return-type annotations (a pre-existing repo-wide gap that `make check`'s `typecheck` target already excludes via not passing `tests/` to mypy), so this isn't something introduced by this change. I'm documenting it here and will note it in the PR description too.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/438

**Branch:** `fix/146-parenthesized-phone-number-error`

**What you built:**
Fixed two bugs in the `phone_us` regex in `safety/pii_scrubber.py` (issue #146) so parenthesized and space-separated US phone numbers are correctly redacted. First, widened each `[-.]?` separator group to `[-. ]?` so space-separated numbers like `(555) 123-4567` match at all, without changing the existing dashed/dotted formats. Second, while testing, found that the leading `(` or `+` was still being left un-redacted even after a number matched. I replaced the regex's leading `\b` anchor with a `(?<!\w)` lookbehind so those characters are now fully consumed by the match.

**Tests added or updated:**
Only `tests/unit/test_pii_scrubber.py` was touched. Extended `test_us_phone_formats` with a no-space parenthesized case (`"(555)123-4567"`). Added `test_phone_number_parens_fully_redacted`, which asserts a full clean replacement (`"Call me at (555) 123-4567"` → `"Call me at [REDACTED]"`) — this covers a second bug found after the initial fix, where the leading `(`/`+` was left dangling un-redacted instead of being consumed by the match. Added `test_space_separated_numbers_false_positive`, which documents a known, accepted tradeoff: widening the separator to include spaces means unrelated 3-3-4 digit sequences (e.g. three separate numbers in a sentence) can now false-positive as a phone number.

**Self-review confirmation:** [X] make check passes  [X] make test-unit passes

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reflection

**What was harder than you expected?**
At first I thought it was going to be a simple 3-line regex change but when I was going to open a pull request I realized that my fix had a slight bug (it was supposed to redact phone numbers to `[REDACTED]` but it would leave a "(" in front). I had to go back through the code and realize that this second fix could still be considered within the reasonable scope and applied that fix as well. Before I could even commit the 1-line regex fix, I had to deal with pre-existing lint debt already in the file. I then got blocked by 409 unrelated pre-existing errors across the whole test suite and I had to figure out that the project's `make check` excludes `tests/` but the local hook doesn't.

**What did you learn about working in a large codebase?**
I learned that passing checks is defined by convention and documentation and not just running every tool to check. That was my initial thought and it took me some time to realize I didn't need every `check/lint` rule to be 100% clean repo-wide. I also learned about scope and having discipline to stick to the scope of the chosen bug. When working on my own projects I can just try and fix every bug I see but to work in a large codebase with known bugs, I have to fix one bug at a time as its own PR. Lastly, I learned that touching one file means inheriting whatever debt already lives there, I don't just fix my lines of code in isolation and any single line of code changed has the potential to impact everything else.

**How did AI tools help — and where did they fall short?**
AI was most useful for fast, mechanical verification at scale like counting all 410 test functions repo-wide to check a claim, diffing exact failing-test sets before and after each change, confirming a reformatted regex was byte-identical to the original. Those are things I could have done by hand but would have been slow and error-prone. It also helped cross-reference scattered project docs that disagreed with each other. `CONTRIBUTING.md`, the `Makefile`, and `pyproject.toml` had different opinions about whether `tests/` should be type-checked, and catching that took reading all three side by side.

Where it fell short: it got a real judgment call wrong at first when it called a second bug I found "out of scope" for the issue. I had to push back and point at the issue's own title before it reconsidered. It also stated a specific fact (409 test functions lacking annotations) that had already gone stale by the time it mattered, and only got caught because I asked it to double-check itself before that number went into a public PR. That was probably the most useful lesson of the module: AI can be confident and still wrong, and the actual scope decisions, and verifying anything before it goes public, stayed on me the whole time.

**What would you do differently if you started over?**
I would consider picking a harder issue if I started over, but, since this issue wasn't too complex, it allowed me to spend more time better understanding the logistics of entering a new codebase as well as opening a PR. I also would have kept lint-hygiene fixes in their own commit from the start rather than bundling them into the feature commit. Lastly, I would have written the tradeoff-documenting test as soon as I widened the regex, rather than waiting some time and realizing I needed to write another test.

**What are you most proud of from this module?**
Learning lots more about reading an existing codebase, following codebase standards, how to properly title and structure commits, and how to professionally open a PR.