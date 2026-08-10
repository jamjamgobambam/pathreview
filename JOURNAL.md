## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/146

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The PII scrubber's phone number regex in `safety/pii_scrubber.py` handled
separators inconsistently across the pattern — the gap after the optional
parenthesis allowed a space, dash, or dot, but the gap before the final four
digits only allowed a dash or dot, not a space. This meant formats like
`(555) 123-4567` and `+1 555 123 4567` passed through both `scrub()` and
`detect()` completely unredacted, since the regex simply didn't match them.
The fix updates all three separator groups in the `phone_us` pattern to
consistently allow space, dash, dot, or no separator at all, so every common
US phone format is caught. All four tests named in the issue now pass:
test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii,
and test_phone_at_start_of_text.

**Branch name:** fix/146-parenthesized-phone-redaction

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Akhrorxuja/pathreview/commit/7922612

**Reproduction summary:**
Ran the existing unit test suite before fixing the code and confirmed
`test_us_phone_formats` failed on parenthesized and space-separated phone
numbers (e.g. `(555) 123-4567`, `+1 555 123 4567`), which passed through
`scrub()` and `detect()` completely unredacted due to inconsistent
separator handling in the `phone_us` regex.

**PLAN.md link:** https://github.com/Akhrorxuja/pathreview/blob/fix/146-parenthesized-phone-redaction/PLAN.md

**Walkthrough video (recommended):**

**Blockers or open questions:**
Still need to confirm the app runs locally at localhost:5173 — Docker
Desktop install has been delayed by a slow internet connection. No other
open questions on the fix itself; all four named tests pass.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the core fix to the `phone_us` regex in `safety/pii_scrubber.py`,
correcting the inconsistent separator groups so parenthesized and
space-separated phone formats are properly redacted. All four tests named
in issue #146 pass.

**Next steps:**
Run `make check` and `make test-unit` to compare against the pre-existing
baseline on `main`, clean up any lint issues introduced by my own change,
and open the PR for review.

**Blockers:**
Local environment setup took longer than expected (Python version mismatch,
missing Rust toolchain for compiling `cryptography`), but resolved by
installing Python 3.11 and Rust via rustup.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/623

**Branch:** fix/146-parenthesized-phone-redaction

**What you built:**
Fixed the `phone_us` regex in the PII scrubber so it consistently redacts
US phone numbers across all common separator formats (dashes, dots, spaces,
and parentheses), resolving issue #146.

**Tests added or updated:**
No new tests were added — the existing tests in
`tests/unit/test_pii_scrubber.py` already covered the required scenarios.
All four tests named in the issue now pass.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
(No new lint errors or test failures introduced compared to `main`; see
PR description for the full before/after comparison.)

**Draft PR feedback received from:** none

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback came in. Per the Su26 course note, reviewer feedback
is not a feature this term, so no review was expected.

**How you responded:**
N/A — no feedback to respond to. I did post my PR link in the class
Slack channel requesting peer feedback as recommended in Week 9.

---

### Reflection

**What was harder than you expected?**
Getting the local environment running was by far the hardest part of the
whole module — harder than the actual bug fix. My Mac had an outdated
Python (3.9) when the project required 3.11+, my pip version was too old
to do editable installs from a pyproject.toml-only project, and once I
got past that, `cryptography` and `libcst` failed to build because they
needed a Rust compiler I didn't have installed. Each fix uncovered the
next missing piece. The actual code change — fixing an inconsistent
separator pattern in a regex — took a few minutes once I could run the
tests. I underestimated how much of "real" contribution work is just
getting your machine into a state where you can even start.

**What did you learn about working in a large codebase?**
I learned to scope my changes carefully and verify what I actually
touched versus what was already broken. Running `make check` and
`make test-unit` on this project surfaced 182 lint errors and dozens of
failing tests that had nothing to do with my issue. Instead of panicking
or trying to fix everything, I learned to isolate my diff (`git diff
--name-only`), run tools scoped to just my file, and directly compare
`main` against my branch to prove my change introduced zero new
failures. That before/after comparison table ended up being the most
convincing part of my PR description — it's a much stronger argument
than just saying "my tests pass."

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for debugging the regex itself — walking
through exactly why `(?<!\d)` and inconsistent `[-.\s]?` groups caused
certain formats to fail, and for troubleshooting the environment issues
step by step (recognizing that `maturin`/Rust build failures meant a
missing compiler, or that pip's dependency resolution needed a specific
flag). Where it fell short was anything requiring my actual GitHub
account, terminal, or physical machine — no AI tool can install Python
or Rust for you, run `git push`, or click "Create pull request." I also
had to catch and correct an AI-suggested command myself once (creating a
branch inside my home directory instead of inside the actual cloned
repo), which was a good reminder to actually read command output rather
than just copy-pasting blindly.

**What would you do differently if you started over?**
I'd set up my full local dev environment (correct Python version, Rust,
Docker) in Week 7 before even picking an issue, rather than discovering
the gaps midway through Week 9 under deadline pressure. I'd also
double-check early which repository a PR is actually targeting — I
initially opened a PR against my own fork's `main` instead of the
upstream `ascherj/pathreview`, which I only caught because I stopped to
verify the URL instead of assuming it was correct.

**What are you most proud of from this module?**
Diagnosing the actual root cause of the regex bug rather than just
patching the one example format mentioned in the issue title. The issue
was titled around parenthesized numbers, but tracing through the pattern
showed the real problem was inconsistent separator handling across all
three digit groups — which also silently broke `+1 555 123 4567` in a
way the issue never mentioned. Catching that made the fix genuinely
correct instead of narrowly correct.
