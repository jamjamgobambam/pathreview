# Journal

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/soccerthomas/pathreview/commit/f53bbd8

**Reproduction summary:**

Ran the existing test suite and confirmed `test_template_snapshot_content_hash`
passed regardless of template content, since it only checked that the hash
was a 32-character string with no comparison to a fixed baseline. This
confirmed the gap described in the issue: prompt template edits could
happen silently with no test signal, even though prompt content directly
affects review quality.

**PLAN.md link:** https://github.com/soccerthomas/pathreview/blob/fix/prompt-template-snapshot-tests/PLAN.md

**Blockers or open questions:**

Unsure whether the maintainer expects MD5 (matching the original test) or
SHA-256 (what I used) for the hash algorithm — flagging this for review
when I open the PR in Week 9. Also uncertain whether the "soft guard"
nature of this approach (a developer could regenerate the snapshot
baseline without bumping the version) is an acceptable tradeoff or if a
stricter enforcement mechanism is expected.

## Week 9 — Implementation & validation

**Implementation commit:** f53bbd8

**What I changed:**

Implemented snapshot-based checks for the versioned prompt templates so
changes to prompt content produce a test failure instead of silently
passing. The snapshots provide a fixed baseline for detecting unexpected
prompt content changes.

**Testing:**

- `make test-unit`: 53 failed, 381 passed. The failures were distributed
  across unrelated modules; none were reported from the prompt-template
  test file.
- `pytest tests/unit/test_prompt_templates.py -v`: 43 passed.
- `ruff check tests/unit/test_prompt_templates.py`: passed.
- `make check`: did not complete because the repository-wide lint run
  reported failures across unrelated files.

**Self-review:**

Reviewed the changed prompt-template tests and ran targeted tests and
linting. I did not make changes to unrelated modules in response to the
full-suite failures.

**Open questions:**

The implementation uses SHA-256 for the snapshot hashes. I would still
welcome maintainer or peer feedback on whether that is the preferred
algorithm and whether the snapshot baseline should be treated as a soft
guard.

**PR:** To be added after the PR is opened.

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [X] No

**Summary of feedback:**

No reviewer or maintainer feedback was received during the contribution
cycle. Per the Su26 course note, reviewer feedback is not a feature this
term.

**How you responded:**

N/A — there was no feedback to respond to. If feedback is provided later,
I will address any comments that require changes.

---

### Reflection

**What was harder than you expected?**

The implementation itself was fairly small, but understanding what the
existing test was actually proving was harder than I expected. The
original test checked that a generated hash had the expected format, but
it did not compare the hash against a fixed baseline. That meant the test
could pass even when the prompt content changed. I had to trace the
existing prompt template tests and snapshot data before I could make the
test verify the behavior described in the issue.

**What did you learn about working in a large codebase?**

I learned that a passing test does not necessarily mean that it is testing
the behavior that matters. In this case, the existing test looked useful
because it generated and checked a hash, but reading the assertion closely
showed that it did not protect against prompt changes. Working in an
existing repository also meant following the project's existing test
structure instead of designing an entirely new testing approach.

**How did AI tools help — and where did they fall short?**

AI was useful for explaining snapshot testing, hashing, and possible ways
to structure the assertions. It was less reliable when making assumptions
about this specific repository. I had to verify the existing prompt
template implementation, snapshot files, and test behavior directly in the
source before deciding what the test should actually assert. This reinforced
that AI suggestions are useful as a starting point but need to be checked
against the actual codebase.

**What would you do differently if you started over?**

I would inspect the existing test and snapshot implementation more carefully
before deciding on the solution. I initially had an open question about the
hashing approach, and confirming the existing conventions earlier would
have reduced some uncertainty. I would also run the targeted tests earlier
instead of spending as much time thinking about the full repository test
suite.

**What are you most proud of from this module?**

I am most proud that the contribution addresses a subtle testing gap rather
than simply adding another test case. The original test could pass even
when prompt content changed, so it did not provide much protection against
silent prompt drift. The updated snapshot tests make prompt changes visible
to the test suite while keeping the change focused on the existing testing
structure.

**Final validation:**

The targeted prompt-template test suite passed with 43 tests:

`pytest tests/unit/test_prompt_templates.py -v` — 43 passed.

The targeted Ruff check also passed. The full repository test suite reported
53 failures and 381 passing tests, while `make check` reported repository-wide
lint failures. These results were documented rather than attempting unrelated
changes outside the scope of the contribution.