# Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/152

**Issue title:** Faithfulness checker can never mark short claims as supported

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
This bug is in `rag/evaluator/faithfulness_checker.py`, in the part of the RAG pipeline that
checks whether the AI's generated feedback is actually true based on the context it was given
(instead of just making stuff up). It works by breaking the feedback into separate claims (one
per sentence) and checking each one against the context for at least 2 shared meaningful words.
The problem is that short claims, like "Knows Python", only have 1-2 meaningful words in them to
begin with, so they can never hit that "2 shared words" requirement, even when they're
completely correct. So right now, any feedback made up of short, true claims gets scored as
0.0, which makes it look totally unsupported when it's actually fine. A fix would need to make
that "2 words" requirement scale down for shorter claims instead of always requiring 2.

**Selection notes ("Is this right for me?" checklist):**

*Understanding the issue* — In my own words: the faithfulness checker is supposed to catch AI
feedback that isn't actually backed up by the source context, but it requires 2 overlapping
non-stopword tokens between a claim and the context to count it as supported. Short claims
(1-2 meaningful words) can never hit that threshold, so fully accurate short feedback gets
scored 0.0 instead of close to 1.0. Before the fix: a real answer like "Knows Python. Knows
SQL." scores 0.0 even when fully supported. After the fix: that same feedback should score
close to 1.0, while genuinely unsupported claims should still score low.

*Tier fit* — This is my first time contributing to a codebase this size, so I deliberately
stuck to Tier 1 rather than reaching for a Tier 2/3 issue to "challenge myself." The fix is
scoped to one function, `_is_supported()`, in one file.

*Codebase readiness* — I found and read `_is_supported()` and `check()` in
`rag/evaluator/faithfulness_checker.py`, and read through
`tests/unit/test_faithfulness_checker.py` end-to-end. Tests like `test_minimum_overlap_required`
and `test_multiple_claims_varying_support` already exercise this exact overlap logic, so I have
existing tests to check my fix against, and a clear pattern to follow for writing new ones.

*Scope and time* — I checked the issue comments and the cohort ledger's claims for this issue
and I'm comfortable with how many others are working on it. This is a Tier 1 issue localized to
one function, so I'm estimating 3-6 hours of focused work, which fits in the Weeks 8-9 window.
The issue has no "blocked by" references or open dependencies.

I also chose this issue on purpose because it's in the RAG/AI evaluation part of the codebase,
which is the area I have the least experience with, so I wanted to use a low-risk Tier 1 issue
to get more comfortable with that side of the project before attempting anything higher-tier
there.

**Branch name:** fix/152-faithfulness-short-claims

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/SwaroopKamble07/pathreview/commit/b8d71da31631fc6f67c819fb2e27c59ed624dded

**Reproduction summary:**
Added a strict `xfail` unit test that runs `FaithfulnessChecker.check()` on
"Knows Python. Knows SQL well." against context that clearly states the
candidate knows both — it scores 0.0 instead of a high score, confirming
`_is_supported()`'s hardcoded `>= 2` meaningful-overlap requirement can
never be satisfied by short claims. Also found that three pre-existing
tests (`test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, `test_multiple_claims_varying_support`)
independently fail for this exact same root cause.

**PLAN.md link:** [PLAN.md](./PLAN.md) (repo root, this branch)

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
Still deciding the exact scaling formula for the overlap threshold (fixed
`min(2, meaningful_claim_tokens)` vs. a proportional threshold) — see
Risks & unknowns in PLAN.md. Also unsure whether `_extract_claims()`
dropping very short claims entirely (its `len(s.strip()) > 10` filter) is
in scope for #152 or a separate bug; leaving it out of scope for now.
Separately, pre-commit hooks (ruff/mypy) fail on
`tests/unit/test_faithfulness_checker.py` due to pre-existing issues
unrelated to this change — used `--no-verify` for the reproduction commit
and will need to decide how to handle this again in Week 9.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md: `_is_supported()` no longer requires a
hardcoded 2 meaningful-word overlap regardless of claim length. While
implementing, I found the plan's originally-proposed formula
(`min(2, len(meaningful_claim_tokens))`) didn't actually fix the bug —
"Knows Python" has 2 meaningful (non-stopword) tokens, `knows` and
`python`, not 1 as I'd assumed when writing the plan, so it still demanded
2 overlapping words. Switched to a proportional threshold instead —
`min(2, max(1, len(meaningful_claim_tokens) // 2))`, roughly half the
claim's meaningful tokens, floored at 1 and capped at 2 — verified by hand
against every case in the test file before implementing. Removed the
`xfail` marker from the issue #152 reproduction test (now passes for
real), fixed the three related pre-existing failures identified in Week 8
(each needed an assertion update for a specific, documented reason — see
PLAN.md "Plan" section item 4 for details), and added 3 new boundary-case
tests for the edge cases in PLAN.md (single-meaningful-token claim
supported, single-meaningful-token claim unsupported, all-stop-word
claim). Ran `make test-unit` before and after the change (via `git stash`)
to confirm: 53 failed/375 passed/1 xfailed → 50 failed/382 passed, with
the same 49 pre-existing, unrelated failures untouched in both runs.
Reformatted the two files I touched with `black`/`ruff --fix` so my own
changes are clean; left the rest of the codebase's pre-existing
lint/format/mypy issues alone (documented, out of scope).

**Next steps:**
Open the PR as a draft, request peer/mentor review in Slack, address
feedback, then mark ready for review and fill in Check-in 2.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/380

**Branch:** `fix/152-faithfulness-short-claims`

**What you built:**
Fixed `FaithfulnessChecker._is_supported()` (`rag/evaluator/faithfulness_checker.py`)
so the meaningful-word-overlap bar required to mark a claim as "supported"
scales with the claim's own length instead of a fixed `>= 2`, so short-but-true
claims (e.g. "Knows Python") can be marked supported instead of always
scoring 0.0.

**Tests added or updated:**
`tests/unit/test_faithfulness_checker.py` — removed the `xfail` marker
from the issue #152 regression test; updated assertions (with inline
justification) in `test_partial_support_returns_middle_score`,
`test_multiple_context_chunks`, and `test_multiple_claims_varying_support`,
whose fixtures each yield fewer claims than their names/comments assume,
for reasons unrelated to the threshold change itself (documented per-test);
added `test_single_meaningful_token_claim_supported`,
`test_single_meaningful_token_claim_unsupported`, and
`test_all_stop_word_claim_is_unsupported` for the boundary cases in
PLAN.md; corrected the stale comment/assertion in
`test_minimum_overlap_required`.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
_(both with pre-existing, documented exceptions unrelated to this change —
see PR description for the full list; my change introduces no new
failures in either.)_

**Draft PR feedback received from:** none (instructor confirmed no peer feedback was required for this issue)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer or maintainer feedback came in. PR #380 has been open and
marked ready for review since 2026-07-31 with 0 comments and 0 reviews as
of 2026-08-06. My instructor confirmed that peer review was not required
for this issue, and reviewer feedback is not a feature of the Summer 2026
cohort, so this is expected rather than a stalled PR.

The one piece of substantive feedback I did receive was from grading on
the Week 9 submission, and I acted on it rather than letting it sit — see
below.

**How you responded:**
No reviewer comments to respond to. I did act on the Week 9 grading
feedback, which flagged that `test_multiple_claims_varying_support`
asserted a score of `1.0` that was only correct *because of a separate
bug*: "Knows Rust." is exactly 10 characters, so `_extract_claims()`'s
`len(s.strip()) > 10` filter silently dropped it, leaving 2 claims that
both happened to be supported. If anyone later fixed that filter, my test
would have broken confusingly, and the failure would have pointed at the
wrong code.

I took the more resilient of the two options the feedback suggested:
rather than just adding a comment flagging the coupling, I rewrote the
fixture so all three claims clear the length filter
("Strong Python expertise. Experienced Rust developer. Docker
containerization skills."), with two supported and one not. The test now
asserts a genuine 2/3 and exercises "varying support" directly, so it no
longer depends on the extraction bug's behavior at all. Committed as
`a2b1dc5` and pushed to the branch and PR, with the PLAN.md note updated
to match.

---

### Reflection

**What was harder than you expected?**

Discovering that my own plan was wrong. PLAN.md confidently proposed
`required = min(2, len(meaningful_claim_tokens))` on the premise that
"Knows Python" has one meaningful token. It has two — `knows` isn't in
the stop-word list — so `min(2, 2)` still demanded 2 overlapping words
and the reproduction test kept failing after I'd "implemented the fix."
The plan was internally coherent and completely wrong at its root, and I
only found out by running it. I had to pivot mid-implementation to a
proportional threshold, `min(2, max(1, n // 2))`, and verify it by hand
against every case in the test file before trusting it.

The second surprise was that "do the tests pass?" wasn't a yes-or-no
question. The repo had 53 failing unit tests before I touched anything.
That meant I couldn't just run `make test-unit` and read the result — I
had to `git stash` my work, capture a clean baseline (53 failed / 375
passed / 1 xfailed), restore, and re-run to prove my change moved the
number the right way (50 failed / 382 passed) without breaking anything
else. Proving a *negative* — "I didn't make it worse" — took noticeably
more work than writing the fix itself, which was about twelve lines.

Third: the three pre-existing tests I'd identified in Week 8 as failing
"for the same root cause" actually failed for three different reasons,
and I only learned that by digging into each one individually.

**What did you learn about working in a large codebase?**

That existing tests encode assumptions, and the assumptions can be wrong.
`test_multiple_context_chunks` is named as though three context chunks
produce three claims — but the feedback string is a single sentence, so
it yields exactly one claim scored against all three chunks concatenated.
The test name, the inline comment, and the fixture disagreed with each
other, and had for a long time. In my own projects I'd assume a failing
test means my code is broken; here I had to treat the test as a claim to
be verified, not a ground truth.

I also learned that bugs sit next to other bugs, and that scoping is a
real skill. I found two adjacent problems — `_extract_claims()`'s
`> 10` character filter dropping short claims, and a `TypeError` when a
context chunk's text is `None` — and deliberately left both out of scope,
documenting why in PLAN.md and the PR rather than quietly expanding the
change. That turned out to be right, but the grading feedback showed I
hadn't followed it all the way through: it isn't enough to scope a bug
out of your *fix*, you also have to keep it out of your *tests'
assumptions*, or you've coupled yourself to it anyway.

The thing I didn't anticipate at all was diff hygiene. I ran `black` on
the file I was editing, which is what the project's own pre-commit config
does — and it reformatted the entire file, turning a 12-line logic change
into a 40-line diff full of unrelated quote-style and line-wrapping
churn. I reverted it and reapplied only the logic change by hand, keeping
the rest of the file byte-identical. On a solo project running the
formatter is unambiguously correct. On someone else's PR, a reviewer has
to read every line you touched, so making them read 28 lines of
reformatting to find 12 lines of logic is a real cost. Same for the
pre-commit hooks: they failed on ~29 pre-existing missing type
annotations that had nothing to do with me, so I used `--no-verify` and
documented exactly why in the commit message instead of either
"fixing" unrelated files or silently skipping.

**How did AI tools help — and where did they fall short?**

Most useful for orientation and for mechanical verification. I was
working in the RAG evaluation code, the part of the codebase I knew
least, and AI let me find and understand `_is_supported()` and its
callers far faster than reading around would have. The highest-value use
was generating a throwaway script that printed the meaningful-token set
and overlap count for every claim/context pair in the test file. That
turned "I think this formula works" into a table I could actually check
before writing any code, and it's what let me catch the plan's flawed
premise and confirm the replacement formula wouldn't flip any
currently-passing test. It was also genuinely good at the writing-heavy
parts — the PR description, the per-test docstrings explaining *why* an
assertion changed.

Where it fell short is more interesting, and it's a pattern rather than
three separate incidents. AI was consistently confident and consistently
plausible, including when it was wrong, and the failures all took the
same shape: reasoning that's locally valid but built on an unverified
factual premise.

- The Week 8 plan asserted "Knows Python" has one meaningful token. Every
  conclusion that followed was correct *given* that, and the whole chain
  was wrong because of it. Nothing in the plan's tone signalled that the
  premise was the weak link.
- When a test assertion had to change, the first version simply asserted
  the value the code actually produced (`1.0`) and wrote a docstring
  explaining it. That's a true statement about the code and still the
  wrong test — it locked in a number that was only right because of an
  unrelated bug. That's precisely what cost me points in Week 9 grading.
- Running `black` on the whole file was "correct" by the project's config
  and wrong for the change I was making.

The through-line: AI is strong at generating options and explaining
mechanics, and weak at judging which of several true things actually
matters here. Deciding that a passing test can still be a bad test, that
a formatter that improves the file can still hurt the PR, that a
plausible plan needs its premise checked before it's followed — that
judgment had to be mine, and the times I outsourced it are exactly the
times it went wrong. Verification is not a step AI can do on its own
behalf, because a confident wrong answer looks identical to a confident
right one.

**What would you do differently if you started over?**

Three concrete things.

First, I'd verify the plan's central factual claim before writing the
plan around it. One command — tokenizing "Knows Python" and printing the
set — would have caught the miscount in Week 8 instead of Week 9 and
saved the entire mid-implementation pivot. Cheapest possible check,
skipped because the reasoning felt solid.

Second, I'd establish the failing-test baseline on day one, before
touching any code, rather than discovering mid-implementation that 53
tests already fail and having to reconstruct the baseline with `git
stash`. It's the first thing I'd do in an unfamiliar repo now.

Third, whenever a test's expected value has to change, I'd ask "is this
value right, and is it right for the *right reason*?" — not just "does
this match what the code does?" I got the first question right and never
asked the second, which is the whole substance of the feedback I
received. A test that passes for an accidental reason is worse than one
that fails, because it will break later and point at the wrong culprit.

I wouldn't change the issue selection. Deliberately picking a Tier 1 bug
in the area I understood least was the right call — the fix was small
enough that all the difficulty landed in process and judgment rather than
in the algorithm, which is where I actually needed the practice.

**What are you most proud of?**

Documenting the weaknesses in my own fix instead of hiding them. Two
moments specifically. When I found the plan's formula didn't work, I
recorded the pivot *in place* in PLAN.md — leaving the original proposal
visible with an update explaining why it was wrong — instead of quietly
rewriting history to look like I'd planned the right thing all along.
And when I realized the fix necessarily admits new false positives
(a 2–3 token claim now needs only 1 overlapping word, so "Expert Rust
developer" matches Python-only context on the incidental word
"developer"), I added an `xfail` test that asserts the *desired*
behavior and wrote a "Trade-off" section in the PR description with a
table showing exactly what got looser, and invited the reviewer to push
back.

Volunteering the strongest argument against my own PR felt
counterproductive while writing it. But that trade-off is real, a
reviewer would eventually have found it, and a fix whose limitations are
documented is worth more to a maintainer than one that hides them — the
`xfail` test even means the limitation gets flagged automatically if
someone later improves precision. That's the habit from this module I'd
most want to keep.
