# PathReview — Module 3 Journal

## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/147

**Issue title:** Resume section detection fails on text with leading whitespace

**Tier:** [x] Tier 1   [ ] Tier 2   [ ] Tier 3

**Problem summary:**
The resume parser is supposed to detect which sections a resume has — like Experience, Education, and Skills. Right now, detection only works if a section heading sits at the very start of a line. If there's any indentation or spaces in front of the heading, the parser misses it entirely, so an indented resume looks like it has **no sections at all**. This happens in the `_detect_sections` function in `ingestion/parsers/resume_parser.py`. It matters because real resumes are often indented or exported with formatting, so their sections get silently dropped — and everything downstream that depends on the resume's structure gets worse results. A successful fix would detect section headings even when they start with leading whitespace, so indented and formatted resumes are parsed with their sections intact — matching how non-indented resumes already work.

**Selection notes (scope fit):**
I chose a Tier 1 issue because this is my first contribution to a large codebase, and the "Is this right for me?" checklist recommends starting there. Issue #147 fits well: it lives in a single file (`resume_parser.py`), the fix is localized to one function (`_detect_sections`), and there's already a test file (`tests/unit/test_resume_parser.py`) I can model new tests on. I reproduced the bug locally before committing, so I already know what "done" looks like — indented section headings should be detected the same as non-indented ones. A few hours of work is realistic for the Week 8–9 timeline.

**Branch name:** fix/147-resume-section-whitespace

**Setup confirmation:** [ ] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/Divergent-Code/pathreview/commit/b4be6f9

**Reproduction summary:**
I ran `_detect_sections` on resume text whose headings had leading spaces and tabs — it returned zero sections, while the same headings without indentation are detected. I captured this as unit tests (the indented and tab cases fail on the original code).

**PLAN.md link:** https://github.com/Divergent-Code/pathreview/blob/fix/147-resume-section-whitespace/PLAN.md

**Loom walkthrough:** N/A — the walkthrough video is optional and is not part of the Week 8 grading rubric.

**Blockers or open questions:**
Haven't run the full `pytest` suite yet — the local Python venv isn't set up. I verified the fix by running the detection regex directly; will run `pytest` once the environment is built.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix from PLAN.md — updated the four heading patterns in `_detect_sections` to allow leading spaces/tabs — and added three unit tests covering indented headings, tab-indented headings, and a false-positive guard. Also set up the local environment (venv, Docker services, migrations, seed data) so I could run the real test suite.

**Next steps:**
Run the full lint and unit suites against my branch and against `upstream/main`, document any pre-existing failures, then open the PR.

**Blockers:**
Setting up the environment surfaced an unrelated bug: a stray `alembic/__init__.py` shadowed the installed `alembic` package, breaking imports from the repo root.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/328

**Branch:** `fix/147-resume-section-whitespace`

**What you built:**
`_detect_sections` only matched headings anchored at the very start of a line, so indented resumes parsed as having no sections. I updated the four detection patterns to allow leading spaces and tabs after the anchor, keeping the anchors so mid-sentence keywords still aren't matched.

**Tests added or updated:**
`tests/unit/test_resume_parser.py` — three new tests: indented headings detected, tab-indented headings detected, and mid-sentence keywords *not* detected (guards against over-loosening). The fix also repairs three tests that were already failing on `main` for this same bug (`test_detect_sections`, `test_parse_single_column_resume_text`, `test_parse_resume_no_work_experience`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

Measured against `upstream/main`: 53 failed / 375 passed → **50 failed / 381 passed**, with no newly-broken tests and no new `ruff` findings (182 before and after). The two remaining `resume_parser` failures (`test_parse_markdown_resume`, `test_strip_markdown_syntax`) fail identically on `main` and come from a separate `_strip_markdown` bug, so they are out of scope and documented in the PR.

**Draft PR feedback received from:** none

---

**Supporting fix — alembic import shadow:**
While setting up the local environment to get PR-ready, I found and fixed a separate bug in the repo. There was a stray `alembic/__init__.py` that turned the migrations folder into an importable Python package. Whenever a process ran from the repo root, that local package **shadowed the installed `alembic` distribution**, so `from alembic import command` (and other submodules) resolved to the migrations folder and failed. Standard Alembic loads `env.py` and `versions/` by path and doesn't need that file, so I removed it. I verified the real `alembic` now resolves correctly and the project's own migrations still work (`alembic heads` → `002 (head)`).

**Fix commit:** https://github.com/Divergent-Code/pathreview/commit/cdd1ac7

---

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes [ ] No — still awaiting review

**Summary of feedback:**
No maintainer feedback arrived. PR #328 sat open from July 29 with zero comments,
and I asked for review twice in the class Slack — `#tech-help` on July 30 and
`#a201-community-su26` on August 2 — with no response to either. For context,
issue #147 carries 46 comments, all of them students claiming the issue. That is
the shape of a teaching repository during a cohort — one issue drawing dozens of
contributors at once — rather than anything specific to my PR, and the course
notes that maintainer review is not part of the Summer 2026 model.

What I did get was a peer review, from @novamapp on August 2, whose own PR
(#559) I had reviewed earlier the same day.

The suggestion was specific: my fix used `[ \t]*`, which matches ASCII space and
tab only. Resumes extracted with `pypdf` or `pdfplumber` routinely carry
non-breaking spaces instead of ASCII indentation, so those headings were still
being missed. They proposed `[^\S\r\n]*` — any whitespace except carriage return
and newline — which catches the PDF artifacts while still refusing to cross a
line break.

**How you responded:**

I checked the suggestion before accepting it. `[^\S\r\n]*` does catch U+00A0 and
Unicode spaces like U+2002 where `[ \t]*` does not, and my mid-sentence guard
test still passes, which was my concern about widening the class. One claim in
their review is wrong, though: they said the new class also catches zero-width
spaces, and it does not — Python's `re` does not classify U+200B as whitespace,
so `\S` matches it and the negated class excludes it. I said so in my reply,
because agreeing with reasoning I had just measured to be inaccurate would have
put something false in the thread.

I applied it in commit `8775f93` and added
`test_detect_sections_with_unicode_whitespace_indentation`, which I verified
fails on the old pattern and passes on the new one — the same standard I had
just held someone else to. The suite went from 11 passing to 12 in that file,
with the two pre-existing `_strip_markdown` failures unchanged.

That commit needed `--no-verify`. The pre-commit hooks fail on issues that
predate my branch — ruff `B904` at `resume_parser.py:77`, and mypy reporting
missing type annotations on every test function in the test file. Fixing them
would have turned a four-line change into an unrelated cleanup, so I bypassed
the hooks and disclosed it in both the commit message and the PR description
rather than quietly. That felt like the honest version of a decision I would
otherwise have been embarrassed by.

The part worth recording is that this feedback existed because I gave feedback
first. Nothing arrived while I was waiting. Something arrived the same day I
reviewed someone else's work.

Before that, there was nothing to respond to on my own PR, so I went the other
direction and reviewed classmates' work instead — PRs #223, #559 and #583 on
August 2, and #860 on August 4. Mine is the only comment on each of them.

I did not want to comment on code I had only read, so I ran all of them first.

**PR #223** (issue #157) corrects a mislabeled test fixture. I fetched the
branch, confirmed `rag/evaluator/relevance_scorer.py` was identical between
`main` and their branch — verifying their "no production code changes" claim
rather than taking it — and ran the test file on both sides: 1 failed / 18
passed on `main`, 19 passed on the branch. Then I ran the scorer directly on
their new fixture to get the exact value, 0.5. That last step produced my
suggestion: they documented the 2/4 overlap in a comment but left the original
assertion `0.3 < score < 0.9`, which also passes at 0.35 or 0.85. The exact
value lived in a comment that nothing enforced.

**PR #559** (issue #146) widens the PII scrubber's phone-number patterns. Here
running it mattered more. Testing the new regexes against the old ones turned up
three things: the new international pattern backtracks catastrophically — 95.9
seconds on a 30-digit input where the old pattern returns instantly, in a
component that by definition processes text somebody else wrote; reordering
`PII_PATTERNS` so phone comes before email means emails like
`john.5551234567@example.com` now leak the local part instead of being fully
redacted; and adding `\s` to the separator class matches across newlines. I
proposed a replacement pattern for the first one and tested it against four real
international formats before suggesting it, because recommending an unverified
regex would have been the same mistake I was flagging.

**PR #583** (issue #72) adds an offline bias audit. Everything in the
description reproduced exactly — 16 tests pass and the CLI printed the same
numbers as the PR body. My one suggestion was about presentation rather than
correctness: the ground-truth set is 14 samples, so `false_negative_rate=50.0%`
on the origin signal is 1 of 2, and a maintainer will read more precision into a
percentage than 14 samples support.

**PR #860** (issue #34) adds an LLM re-ranking step to the retrieval pipeline. The safety design is careful — the factory returns `None`
without an API key so the feature is opt-in, a failed call falls back to the
original blended score rather than dropping the chunk, and it adds no new
dependency. My finding was in the score parser: it takes the first number in the
model's response and clamps it to `[0, 1]`, so `"I would rate this 8 out of 10"`
scores 1.0, and so does `"Chunk 3 scores 0.4"` — a preamble that happens to
contain a number becomes maximum relevance. I ran those cases rather than
reasoning about the regex, because the failure only shows up on inputs the
prompt is trying to prevent.

There was a second problem with that PR that I raised privately instead. It is
the kind of mistake that is quick to fix and unpleasant to have pointed out in
public, and the review itself did not need it. Choosing the channel turned out
to be part of giving the feedback.

In all four I also said what I thought was done well, because a review that is
only criticism is not much use.

**What came of them.** All four authors acted on the review — three replied in
the thread, and the fourth answered in code. I checked the diffs rather than
taking the replies at face value.

On #559, three of my four points were acted on. `phone_intl` is now
`\+[0-9](?:[-.\s]?[0-9]){7,14}\b`, which consumes one digit per repetition and
so has nothing to backtrack through; `email` has been restored above the phone
patterns; the 4.6 MB video is gone behind a new `.gitignore` rule; and they
added regression tests so the same class of change cannot slip back in. The
fourth point they declined, and they were right to. On the `\s`-matches-newline
finding they wrote that they were keeping it "since I agree that over-redaction
is the safer direction for a scrubber" — using the framing from my own comment
to disagree with the suggestion attached to it. A reviewer whose every
suggestion is accepted is not being read carefully.

On #583 both points landed in commit `123fb47`. Every rate now prints its counts
— `false_negative_rate=50.0% (1/2)`, `[education] 100.0% (4/4)`, with `n/a (0/0)`
where the denominator is zero — with three new tests covering the rendering, and
the accidental `package-lock.json` deletions are reverted. The author also
pushed back on the part of my point I had left open: showing counts mitigates a
14-sample ground truth rather than fixing it, and expanding the labeled set to
40–50 samples belongs in its own PR. That is the correct call, and it is scoping
rather than deferring.

On #223 the assertion is now `assert score == 0.5` instead of the original range,
with a comment explaining why. The author ran the scorer directly before making
the change rather than trusting my number — which is the same verification step
I had used to find it, arrived at independently.

On #860 there was no reply in the thread, but commit `4c552661` addresses all
three code findings. `_parse_score` is replaced by a JSON-array parser that
routes out-of-range values to the original blended score instead of clamping
them to 1.0; the per-chunk calls are batched into a single numbered prompt; and
`temperature=0` is set. The test suite went from 9 tests to 21, with a
`TestParseScores` class aimed at the parsing cases the review named.

The thing I did not expect is that this is where my own feedback came from.
@novamapp reviewed my PR the same day I reviewed theirs. Waiting produced
nothing for a week; reviewing produced a review within hours. In a cohort all
working the same repository at the same time, the people best placed to read my
change carefully were the other students — and the way to get read was to read
someone else first.

---

### Reflection

**What was harder than you expected?**

The fix itself was four lines. Each of the four regex patterns in
`_detect_sections` gained `[ \t]*` after its anchor. That was it. Everything
that took real time was around it.

Setting up the environment was the actual work — venv, Docker services,
migrations, seed data. It was hard enough that in Week 8 I submitted a plan
while recording the blocker in my own journal: I had not run `pytest` yet
because the venv was not built, so I verified the fix by running the detection
regex directly instead.

The part I did not anticipate at all was that 53 tests were already failing
before I touched anything. On my own projects a red suite means I broke
something. Here it meant nothing until I had a baseline to compare against. I
expected the difficulty to be in writing the code. It was in working out what
"working" even meant in a repository I did not write.

**What did you learn about working in a large codebase?**

That attribution is a skill, and that a bug report is a hypothesis rather than a
fact.

On attribution: I ran lint and the unit suite against my branch and against
`upstream/main` so I could tell my breakage from the repository's. The result —
53 failed / 375 passed becoming 50 failed / 381 passed, with ruff findings at
182 on both sides — only means something because I took the baseline first.
Without it I would have had a number and no way to read it.

On bug reports: reviewing PR #223 taught me this better than my own issue did.
Issue #157 said the relevance scorer was broken. It was not. The scorer
correctly returned 1.0, and the *test fixture* was mislabeled — it claimed
partial overlap while containing every query term. Shi-Tao found that by reading
the captured log line rather than trusting the title. My issue, #147, pointed at
`_detect_sections` and the bug was exactly there. Two students, the same
repository, the same week, and only one of the two issue reports pointed at the
right file. The only thing that separated them was reproducing before believing.

Reviewing four PRs made the same point four times. In every one, the thing worth
saying only existed because I ran the code — an exact score of 0.5, a regex that
takes 95 seconds on a 30-digit string, a percentage resting on two samples, a
score parser that reads "8 out of 10" as perfect relevance. None of those are
visible in a diff. Reading a change tells you what it was meant to do; running
it tells you what it does.

The third thing is that scope is a judgment, not a rule. Two failures in the
same file I was editing — `test_parse_markdown_resume` and
`test_strip_markdown_syntax` — come from a separate `_strip_markdown` bug. I
left them alone and documented why in the PR. But I did fix a stray
`alembic/__init__.py` that was shadowing the installed `alembic` package,
because that one blocked me from running anything. Fix what blocks you, document
what does not.

**How did AI tools help — and where did they fall short?**

I used one tool for this module — Claude Code — and I used it heavily. The
implementation is largely generated. That is worth saying plainly before
anything else, because the interesting part is not whether I used it but where
the line between us actually fell.

Where it helped most was anything mechanical and verifiable. Drafting the regex
change and the tests in the style of the existing file. Working out the alembic
import shadow, which needed reasoning about Python resolving a local directory
ahead of an installed distribution — I would have got there eventually, but not
in one evening. And later, writing throwaway scripts to measure things: timing a
regex against inputs of growing length, diffing one pattern's behaviour against
another across a table of cases. Those are tedious to write by hand and they are
what turned "this looks risky" into "this takes 95 seconds at 30 digits."

Three places it fell short, in increasing order of how much they mattered.

The smallest is mechanical failure. While posting a review reply, it took four
attempts to produce a comment that rendered correctly, because invisible Unicode
characters kept surviving through shell and Python escaping layers. It was
confidently wrong twice about having fixed it, and only a byte-level check
settled it. That is a useful shape to recognise: a tool can be certain and
mistaken at the same time, and the fix was to stop asking and start measuring.

The middle one is that it accepts a plausible framing and builds on it. Issue
#157, which I met while reviewing a classmate's PR, is the clean example — a
confident, wrong title pointing at the relevance scorer when the bug was in the
test fixture. Handed that title without the reproduction, a model would produce
a competent fix to the wrong file. The protection is not a better prompt. It is
running the thing first.

The one that mattered most is scope. Every scoping decision in this contribution
was a judgment about someone else's codebase, and none of them came from the
tool. Leaving `_strip_markdown` alone even though it was in the file I had open.
Fixing alembic even though it had nothing to do with #147. Leaving 182 ruff
findings untouched. Deciding to bypass the pre-commit hooks rather than
type-annotate fifteen test functions I did not write. In several of those the
tool offered a reasonable case for the other choice, and the reason I did not
take it was that I had spent enough time in the repository to know what a guest
should and should not touch. A model will generate a change. It will not tell
you whether the change is the right size for a project you are visiting.

The honest summary is that the code is AI-written and the decisions are mine,
and I only know that is true because I can name the specific places I overrode
it.

**What would you do differently if you started over?**

Set up the environment before writing the plan, not after.

I planned and reproduced in Week 8 while the venv was still not built, and
verified by running the regex directly instead of the test suite. It worked, but
"the regex now matches" is weaker proof than "the suite is green," and I only
got the stronger proof a week later. The alembic bug also surfaced during Week 9
setup, on the way to a deadline. Found in Week 7, it would have been an
afternoon rather than a blocker.

The smaller thing is commit hygiene. My reproduction commit, `b4be6f9`, carries
both the failing tests and the fix. Splitting "prove the bug" and "fix the bug"
into two commits would let a reviewer see the red state without checking out an
earlier revision.

One thing I would not change is the tier. A Tier 1 issue was the right choice
for a first contribution to a codebase this size, and the amount I learned came
from the process around the fix rather than from the difficulty of the fix.

**What are you most proud of from this module?**

The false-positive guard test.

Loosening a regex anchor is the kind of change that can quietly start matching
things it should not. I named that risk in `PLAN.md` before writing any code,
with the mitigation stated — keep the `^` and `\n` anchors, add only `[ \t]*`
after them — and then wrote
`test_detect_sections_ignores_midsentence_keyword` to enforce it. It asserts
that "My proudest experience: shipping a product." does *not* register an
Experience section.

Most of the tests I have written prove that a change works. That one proves the
change does not work too well, and it exists because I wrote down what I was
afraid of before I had anything to be afraid of yet.
