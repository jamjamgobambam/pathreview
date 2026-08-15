## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/150

**Issue title:** Tech detector counts vendored and build-output files, skewing language detection

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem Summary:**

The TechDetector tool in agent/tools/tech_detector.py is supposed to
ignore files inside vendor/build folders like node_modules/ and build/
when detecting a repository's primary programming language. However,
its skip-list checks for patterns like "/node_modules/" with a leading
slash, while file paths passed into the tool (e.g. "node_modules/lib/index.js")
often don't have that leading slash. Because of this mismatch, those
files are never filtered out and get counted as if they were part of
the actual codebase. As a result, a repo that is mostly Python can be
incorrectly reported as "primarily JavaScript" just because it has a
few bundled JS dependency files. Fixing this means correcting the skip
logic so it matches these paths regardless of a leading slash, restoring
accurate language detection.

**Branch name:** fix/150-tech-detector-vendored-files

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

**Selection notes ("Is this right for me?" checklist):**

I chose Tier 1 issue #150 over #153 (also Tier 1) because it involves a
single, well-contained bug in one file (agent/tools/tech_detector.py),
has clear reproduction steps and named failing tests, and touches the
agent/ area of the codebase, which interests me. I avoided #153 for a
different reason: it had an unusually high number of claims and several
already-open pull requests, and I wanted to reduce the temptation to
reference existing solutions before reasoning through the bug myself.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/DataMnk/pathreview/commit/939b152

**Reproduction summary:**
I reproduced the bug locally using the Python REPL with the exact steps
from the issue: `TechDetector().execute({'files': [...]})` with a file
list containing `node_modules/lib/index.js` and `build/bundle.js` among
Python files. The result's `primary_language` came back as `JavaScript`
instead of the expected `Python`, confirming that `_should_skip_file()`
fails to filter out these vendored/build paths because it checks for
patterns with a leading slash (e.g. `"/node_modules/"`) that don't match
paths without one (e.g. `"node_modules/lib/index.js"`).

**PLAN.md link:** https://github.com/DataMnk/pathreview/blob/fix/150-tech-detector-vendored-files/PLAN.md

**Blockers or open questions:**
None major yet. I still need to confirm whether file paths can ever arrive
with backslashes instead of forward slashes on Windows, but I don't
expect this to block the fix in Week 9.

## Week 9 — Check-in 1 (mid-week)

**Date:** July 30, 2026

**Progress:**
Implemented the fix in `_should_skip_file()` (`agent/tools/tech_detector.py`,
commit `499f202`): instead of substring-matching slash-anchored patterns like
`"/node_modules/"`, the method now splits each filepath into path segments and
checks whether any directory segment (excluding the filename) exactly matches
a known vendor/build directory name. This correctly excludes paths with or
without a leading slash, while avoiding false positives like
`src/node_modules_helper.py`.

**Verification so far:**
- Both previously-failing tests now pass: `test_node_modules_excluded` and
  `test_build_directory_excluded`
- Full test suite for the file passes: 27/27 tests
- Manually re-ran the original reproduction steps from the issue — confirmed
  `primary_language` now returns `"Python"` instead of `"JavaScript"`
- `ruff check agent/tools/tech_detector.py` passes with no errors

**Remaining for this week:**
- Write PR description following the project's contribution standards
- Open the pull request
- Add regression tests for the edge cases identified in PLAN.md
- Final Week 9 check-in with PR link

## Week 9 — Check-in 2 (end of week)

**Date:** August 4, 2026

**Branch:** fix/150-tech-detector-vendored-files

**Pull Request:** https://github.com/ascherj/pathreview/pull/804

**Summary:**
Opened PR #804 against `ascherj/pathreview:main`, closing issue #150.

**Self-review against the seven conditions for "done":**
- [x] The fix works — confirmed against the bug spec (reproduction steps
      from the issue now return `"Python"` instead of `"JavaScript"`)
- [x] Existing tests still pass — full suite is 27/27
- [x] New tests are written — the two previously-failing named tests
      (`test_node_modules_excluded`, `test_build_directory_excluded`) pass,
      and I added three new regression tests covering the edge cases
      identified in PLAN.md: a lookalike filename that should NOT be
      excluded, a `build/vendor.js` path, and Windows backslash paths.
      Full suite is now 30/30.
- [x] The code follows codebase conventions — docstrings and comment style
      match the rest of `tech_detector.py`
- [x] The linter passes — `ruff check agent/tools/tech_detector.py` is clean
- [x] Documentation is updated — inline comment explains the root cause and
      the fix for future contributors
- [x] The PR description is written — all template sections filled in with
      real content, not placeholders

**Tests documented:**
- `test_node_modules_excluded` and `test_build_directory_excluded` (both
  pre-existing, previously failing) now pass with the fix
- Full file suite: 27/27 passing
- Manual verification in the Python REPL against the original issue
  reproduction steps
- Three new regression tests added for edge cases from PLAN.md — all
  passing. Full suite: 30/30

**Blockers or open questions:**
None blocking. Finishing edge-case test coverage before final resubmission.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback has come in on PR #804. Per the course's Summer 2026
note, reviewer feedback is not a feature this term, so this is expected.

**How you responded:**
N/A — no feedback to respond to.

---

### Reflection

**What was harder than you expected?**
Well, this is the first time that I work in a big collaborative project
like this one. This semester was particularly challenging: the content,
the rhythm, the length. From the beginning the technical part needed
some extra work — I had to download and install Docker and prepare the
environment, do some reading.

**What did you learn about working in a large codebase?**
It was a project that needed guidance; the class Q&A was very helpful.
The fix itself was relatively simple — dividing some strings and doing
some checkups — which alone would have been simple enough, however
embedded in such a big project there is a lot of code reading that needs
to be done before even touching anything. Then the testing part was fun,
and being able to write new tests was also interesting. A great learning
opportunity in general.

**How did AI tools help — and where did they fall short?**
Claude helped understanding the git collaboration process in general. It
was necessary to stay in the loop and understand the codebase to be able
to ask the right questions and not letting it deviate from the purpose
or the goal, which was to actually learn how to participate and
collaborate in GitHub effectively. For example: when the linter flagged
181 errors across the whole repo, I couldn't just take Claude's word that
they weren't mine — I had to actually check the output myself to confirm
none of those errors were in my file before deciding `--no-verify` was
the right call, backed by what Margaret had confirmed in class Q&A, not
just Claude's suggestion.

**What would you do differently if you started over?**
I think overall it was a good experience — next time I'll know some
things better. Given the knowledge and time I had, I think it was a good
journey. I feel tempted to say "if I had more time..." but that doesn't
happen in real life — time is always short, so it's important to learn
to do everything consciously every time, or as much as possible.

**What are you most proud of from this module?**
I feel more proud of actually having pushed through until the end, of
having persevered, because this semester was particularly difficult on
so many levels. I'm glad it's over and I hope things get better over
Fall. I'm proud that I managed to push through till the end. I almost
missed these final reflection questions, but here I am. I think we
learned a lot and it's all very relevant.