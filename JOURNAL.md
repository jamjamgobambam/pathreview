
## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/151

**Issue title:** Bias detector patterns are too narrow to match common phrasings

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Scope-fit reasoning:**
Using the "Is this right for me?" checklist: the issue is scoped to a single
file (`bias_detector.py`), the fix is behavioral rather than architectural
(extending pattern matching, not redesigning a system), and there's an
existing test suite (9 failing tests) that defines exactly what "done"
looks like — which removes a lot of ambiguity for a first issue in an
unfamiliar codebase. It's labeled `tier-1` and doesn't touch other services
(no auth, no DB schema changes), so the blast radius if I get something
wrong is small. I chose it over other Tier 1 options specifically because
the failing tests give me a concrete, checkable definition of success
rather than open-ended judgment calls about what "good enough" means.

**Problem summary:**
The bias detector module currently relies on regex patterns that only match
specific, near-exact phrasings of biased language, like "bootcamp graduates
lack rigor." It misses equivalent statements that express the same bias in
different words — for example, calling out someone's education informally or
making age-based assumptions about their ability to keep up with new tools.
Because the matching is too rigid, real instances of dismissive or
discriminatory language slip through undetected, which defeats the purpose
of a safety-layer component. Nine existing unit tests already define the
expected coverage and are currently failing, so a successful fix means
broadening the detection logic (likely moving from exact-phrase regex toward
more flexible pattern or keyword-based matching) until those tests pass
without introducing false positives on neutral text.

**Branch name:** fix/151-bias-detector-pattern-matching

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 9 — Implementation

### Check-in 1

**Current progress:**
Implemented the clause-based matching strategy described in PLAN.md and began updating the regex patterns to match protected-category terms and negative framing within the same clause.

**Testing:**
- Initial unit tests run to verify existing failures.
- Continued iterating against the failing bias detector tests.

**Blockers:**
Still refining pattern matching to eliminate remaining failing tests without introducing regressions.

### Check-in 2

**Current progress:**
Implemented the fix for issue #151 in `safety/bias_detector.py` — replaced
the exact-phrase regex approach with clause-level matching: a clause is
flagged only when it contains both a protected-category term (educational
background, age, or socioeconomic/national background) and a dismissive
or negative-capability term. This directly addresses the root cause traced
in PLAN.md (patterns anchored to singular nouns, specific verbs like
"is"/"lack", and rigid connective phrases like "person from").

Also fixed one regression caught during testing: the original
`(?:equal|comparable)` negative pattern only matched "not equal/comparable
to" and missed "never equal/comparable to" — added "never" as an
alternative.

**Testing:**
- `pytest tests/unit/test_bias_detector.py -v` — 32/32 passing (all 9
  originally-failing tests now pass; all 23 originally-passing tests
  still pass, confirming no regressions)
- `make check` — passing (ruff, black, mypy all clean)
- `make test-unit` — passing

**Manual verification:**
Re-ran the original repro from issue #151:
> "The candidate only attended a bootcamp, so this project lacks the rigor of a formal CS education"

Previously returned `(False, '')`. Now correctly returns
`(True, "Dismissive language about educational background")`.

**PR status:**
Opened as draft: https://github.com/arshadshiju/pathreview/pull/1
Branch: `fix/151-bias-detector-pattern-matching`
Commit: `fdb1cd7`

**Next steps:**
Get peer feedback on the draft PR, address any review comments, then mark
ready for final review.

**Blockers:**
None currently.
## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review (not a feature in Summer 2026)

**Summary of feedback:**
No reviewer feedback was available this term, per the course note. PR #1
remains open as a draft on branch `fix/151-bias-detector-pattern-matching`.

**How you responded:**
N/A — no feedback arrived to respond to.

---

### Reflection

**What was harder than you expected?**
Getting the local environment stable was harder than the actual bug fix.
Between Docker container startup, `python` vs `python3` aliasing on macOS,
a bcrypt/passlib version mismatch throwing warnings on every login, and
zsh choking on heredocs when paste-buffering split mid-command, I spent
more real time on environment friction than on writing the regex fix
itself. I didn't expect terminal mechanics — quoting, heredoc boundaries,
pre-commit hooks stashing unstaged changes mid-commit — to be where most
of the debugging happened, rather than the Python logic.

**What did you learn about working in a large codebase?**
The failing tests told a much more precise story than the issue
description did. Reading the issue, I expected "the regex needs to be
broader." Actually tracing each of the 9 failing tests against the real
`DISMISSIVE_PATTERNS`/`DEMOGRAPHIC_PATTERNS` regexes showed the bug was
narrower and weirder than that — singular-only nouns ("developer" but not
"developers"), a required literal "is" before "lacks," a hardcoded
"person from" phrase that didn't match "developers from." None of that
was visible from the issue text alone; it only showed up by running the
actual test suite and reading assertion failures one by one. I also
learned that a fix which passes the tests you're targeting can quietly
break tests you weren't looking at — my first version flipped
`test_self_taught_comparison_detected` from passing to failing because
I'd only added "not equal/comparable to" and missed "never equal/comparable
to." Existing test coverage is what caught that regression, not my own
review of the diff.

**How did AI tools help — and where did they fall short?**
AI was most useful at exactly the step I found least interesting to do by
hand: tracing 9 failing tests against 7 regex patterns to find the precise
mismatch in each one, then generalizing that into a single coherent
matching strategy (category term + negative term co-occurring in the same
clause) instead of patching each regex individually. It also helped
structure the reproduction evidence and PLAN.md into something scoped to
the actual grading rubric rather than a vague restatement of the issue.

Where it fell short: it couldn't see my full test file up front, so its
first draft of the fix was an educated guess that got one edge case wrong
(the "never" vs "not" gap) — it took an actual test run to catch that, not
foresight. It also couldn't run anything in my environment, so every
heredoc paste failure, pre-commit hook stash, or `sed` quoting issue on
macOS had to be diagnosed from pasted terminal output after the fact,
which is slower than debugging it live would have been.

**What would you do differently if you started over?**
I'd paste and verify the full test file content earlier, before writing
any fix, instead of tracing failures from pytest output alone — I could
have skipped one whole round of "fix broke a passing test" if I'd had the
complete picture up front. I'd also copy multi-line heredocs from a plain
text buffer instead of relying on terminal scrollback paste, since that's
what caused the file corruption partway through Week 9.

**What are you most proud of from this module?**
Root-causing all 9 failures individually before writing any code. It
would have been faster to just throw a looser regex at the problem and
see what stuck, but going test-by-test and identifying that each failure
had a distinct, specific structural cause (missing plural, missing verb
form, missing connective phrase) is what let the actual fix generalize
correctly on close to the first try, rather than needing several more
rounds of regex whack-a-mole.
