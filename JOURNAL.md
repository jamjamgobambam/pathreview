## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/148

**Issue title:** Skill extractor fails to detect JavaScript and TypeScript

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The `extract_skills()` function in `ingestion/parsers/skill_extractor.py` fails to correctly identify JavaScript and TypeScript in submitted text. JavaScript-related content returns no detections at all, while TypeScript content (even when explicitly mentioning `.ts`/`.tsx` files and the word "TypeScript") is only partially detected as "React," missing the TypeScript skill itself. This suggests the language-detection patterns for the JS/TS family are missing or broken, while similar detection for Python, DevOps, and database skills works correctly. A successful fix would update the detection logic so JavaScript and TypeScript are properly recognized, with the related failing unit tests passing.

**Branch name:** fix/148-js-ts-skill-detection

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/shresthapresto/pathreview/commit/2042e21b48e27b48894df564fee54d919ac6d397

**Reproduction summary:**
Ran `pytest tests/unit/test_skill_extractor.py -k "test_javascript_detection or test_text_with_typescript_files" -v` locally and confirmed both tests fail. `test_javascript_detection` fails because `require('fs')` has no space after `require`, so the detection regex `\b(import|require)\s+` never matches. `test_text_with_typescript_files` fails because TypeScript syntax (`export interface`, `export class`, `Promise<User>`) isn't recognized by any TS-specific pattern, and no false-positive React match occurs in this case since the text doesn't mention `.tsx`/`.jsx`.

Test output:
```
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_text_with_typescript_files - assert False
FAILED tests/unit/test_skill_extractor.py::TestSkillExtractor::test_javascript_detection - assert False
2 failed, 16 deselected in 2.05s
```

**PLAN.md link:** https://github.com/shresthapresto/pathreview/blob/fix/148-js-ts-skill-detection/PLAN.md

**Walkthrough video (recommended):** Not recorded

**Blockers or open questions:**
Still need to confirm whether `test_devops_tool_detection` and `test_docker_compose_detection` failures (mentioned in the original issue) share the same root cause or are separate — haven't reproduced those yet.

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Implemented the fix in `ingestion/parsers/skill_extractor.py` — added JS/TS syntax
pattern detection, TypeScript-specific patterns, removed the .tsx/.jsx false-positive
React trigger, and added Dockerfile/docker-compose syntax detection. All 4 target
failing tests now pass. Ran full test suite — 49 failed/379 passed, down from the
53/375 baseline, confirming no regressions. Ran make check and make test-unit to
confirm a clean diff. Opened draft PR #898.

**Next steps:**
Share PR in Slack for peer/mentor feedback, address any feedback received, mark PR
as ready for review, and complete Check-in 2 by Sunday.

**Blockers:**
None currently.

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/898

**Branch:** fix/148-js-ts-skill-detection

**What you built:**
Fixed JavaScript and TypeScript detection in the skill extractor by adding proper
syntax pattern matching (beyond the previous import/require-with-whitespace check),
separated TypeScript-specific detection from generic JavaScript detection, removed
a false-positive React trigger caused by .tsx/.jsx filename mentions, and added
Dockerfile/docker-compose syntax detection that doesn't require the literal word
"docker" to appear in the text.

**Tests added or updated:**
No new test files added. Existing tests in tests/unit/test_skill_extractor.py —
test_javascript_detection, test_text_with_typescript_files, test_devops_tool_detection,
and test_docker_compose_detection — now pass and cover this fix. test_react_detection
also still passes, confirming no regression to existing React detection.

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes

**Draft PR feedback received from:** none yet (submitting slightly late; will incorporate any feedback that comes in)

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviewer feedback was received. Per the course's Su26 note, reviewer feedback
was not an active feature this term.

**How you responded:**
N/A — no feedback was received to respond to.

---

### Reflection

**What was harder than you expected?**
Getting the local environment running took far longer than the actual code fix.
I hit a chain of issues just to get Docker Desktop working — it wasn't installed,
then failed with a "virtualization not detected" error that turned out to require
enabling Virtual Machine Platform in Windows and virtualization in BIOS. Then I had
to sort out `make` not existing on Windows, install it via winget, and switch from
PowerShell to Git Bash since many commands only worked there. By the time I could
actually run `make setup` and `make run`, I'd spent more time on tooling than on
understanding the bug itself. It was a good reminder that "environment setup" is a
real skill, not a formality to skip past.

**What did you learn about working in a large codebase?**
Reproducing the issue precisely before touching any code made a huge difference —
running the exact failing tests first showed me exactly what was expected vs. actual,
instead of guessing. I also learned that a fix isn't just "make the failing test pass" —
I had to check the full test suite (`make test-unit`) and lint/type checks (`make check`)
before and after my change to prove I didn't break anything else. The codebase had 53
pre-existing failing tests and 182 pre-existing lint errors that had nothing to do with
my issue, and distinguishing "pre-existing and out of scope" from "caused by my change"
was an important discipline I hadn't had to practice before.

**How did AI tools help — and where did they fall short?**
AI was most useful for diagnosing the root cause quickly — reading the regex patterns
in the skill extractor and explaining exactly why `require('fs')` didn't match
`\b(import|require)\s+` (no space before the parenthesis), and why `.tsx`/`.jsx` filename
mentions were causing false-positive React detections. It also helped me write the new
detection patterns and catch a whitespace bug in my own Dockerfile regex before I wasted
time debugging it manually. Where it fell short: it couldn't run commands for me or see
my actual terminal state, so a lot of back-and-forth was just me pasting error output
and getting the next step — useful, but slower than if I'd understood the Windows/Docker/
Git Bash toolchain better going in.

**What would you do differently if you started over?**
I'd set up and verify my full local environment (Docker, WSL2, virtualization, Git Bash,
`make`) before browsing the issue tracker at all, instead of discovering each missing
piece one at a time while trying to move forward. I'd also check the linked PRs on an
issue before claiming it, to confirm it wasn't already being solved by someone else.

**What are you most proud of from this module?**
Getting a clean, root-cause fix rather than a surface patch — the JS/TS detection bug
had a real underlying reason (an overly narrow regex and unrelated false-positive
trigger), and I traced it down to that instead of just special-casing the failing test
inputs. Confirming with the full test suite that I introduced zero new failures felt
like real engineering discipline, not just "make the assignment pass."