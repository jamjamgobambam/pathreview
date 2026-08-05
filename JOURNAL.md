## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received on PR #746 by the end of the module.
Per the Su26 course note, reviewer feedback is not a feature this term. I
did post in the cohort Slack channel asking for a quick look at the PR
before finalizing it, but did not receive a response by the deadline.

**How you responded:**
N/A — no feedback was received to respond to.

---

### Reflection

**What was harder than you expected?**
The actual regex fix was small and quick once I identified the root cause,
but getting my local environment fully working was harder than expected.
Running the test suite surfaced several missing dependencies unrelated to
my change (`rank_bm25`, `tiktoken`, `passlib`, `jose`), which caused
unrelated test files to fail at collection and made it hard to tell at
first whether my change had broken something or whether the environment
itself was incomplete. I also hit a small but confusing git issue where the
branch name I intended to push didn't match the branch git had actually
created from my commit, which blocked my first push attempt.

**What did you learn about working in a large codebase?**
I learned that not every red X or failing test is your responsibility to
fix — part of contributing to an existing codebase is distinguishing
between problems your change introduced and problems that were already
there. I used `git stash` to temporarily revert my change and confirm that
one failing test (`test_mixed_pii_and_text`) failed identically on `main`,
which let me document it honestly as pre-existing rather than either
ignoring it or trying to fix something out of scope for my issue. I also
learned to scope lint/test runs to the specific file I changed rather than
running the entire suite, since a codebase this size will always have some
unrelated debt.

**How did AI tools help — and where did they fall short?**
AI assistance was most useful for quickly identifying the root cause in the
regex (the separator character class only allowed dashes/dots, not
whitespace) and for drafting the fix, PR description, and test commands
without me needing to look up exact regex syntax or PR template conventions
from scratch. Where it fell short was in verifying the environment and
distinguishing my change's actual effects from the environment's
pre-existing gaps — that required me to actually run commands, read
tracebacks, and use `git stash` to isolate the failure myself. AI could
suggest what to try, but confirming the pre-existing bug and getting the
environment set up correctly required my own hands-on debugging.

**What would you do differently if you started over?**
I'd run the full test suite and confirm my environment was completely set
up before writing any code, rather than discovering missing dependencies
partway through. I'd also confirm my branch name matched what git actually
created before attempting to push, to avoid the wasted round-trip.

**What are you most proud of from this module?**
I'm most proud of taking the time to actually verify the `test_mixed_pii_and_text`
failure was pre-existing instead of assuming it or panicking about it — using
`git stash` to isolate my change and confirm the failure existed on `main`
gave me a real answer instead of a guess, and let me document it honestly in
the PR rather than hiding it or over-claiming my fix broke something.