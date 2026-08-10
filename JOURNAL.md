## Week 7 — Issue selection

**Issue link:** [https://github.com/ascherj/pathreview/issues/146](https://github.com/ascherj/pathreview/issues/146)

**Issue title:** PII scrubber fails to redact parenthesized US phone numbers

**Tier:** [x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The code used to hide sensitive personal information is currently missing a common phone number format: parenthesized US phone numbers. 

While it successfully catches numbers formatted with dashes (like 555-123-4567), it overlooks numbers written with parentheses (like (555) 123-4567). 

Because of this gap, parenthesized phone numbers slip through the system without being hidden or flagged as private data. A successful fix will make sure this standard phone number style is properly protected.

**Branch name:** [paste branch name here]

**Setup confirmation:** [x] App runs locally at localhost:5173

**Cohort ledger:** [x] Issue added to cohort ledger

---

## Is This Issue Right for Me?

### Part 1 — Understanding the Issue
- [x] Can I explain what this issue is asking for in my own words?
- [x] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.
- [x] Do I understand which part of the app is affected?
- [x] I've located the relevant files and confirmed they exist in the codebase.
- [x] Do I understand what "done" looks like?
- [x] Can you describe what the app should do (or not do) once the issue is fixed? 
- [x] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

### Part 2 — Tier Fit
Issues in the tracker are tagged with a tier level. Here's what each one means:

#### Tier	Description	Typical scope
_Tier 1	Self-contained, localized fix. The change lives in one or two files and doesn't require understanding how the whole system fits together.	Bug fix, missing validation, broken test, documentation update_

_Tier 2	Requires understanding how two or more modules interact. May involve a service layer, database model, or API endpoint.	Feature addition, refactor, data flow bug_

_Tier 3	Requires understanding the full system — multiple modules, possibly infrastructure or AI pipeline changes.	Architecture change, cross-cutting behavior, RAG or agent modification_

- [x] Is the tier a realistic match for where I am right now?

### Part 3 — Codebase Readiness

_Can I find the relevant code?_

- [x] I've found and read the specific code the issue references (not just the file — the function or section).
Do I understand the surrounding code well enough to change it safely?
- [x] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.
- [x] I've found the test file for my module and read at least one test end-to-end.

### Part 4 — Scope and Time

- [x] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.
- [x] Is the scope realistic for Weeks 8–9?
- [x] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.
- [x] This issue has no open blockers or dependencies on other unresolved issues.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** 
__[link to commit documenting the reproduced issue]__

[Commit 5d1ee4c](https://github.com/novamapp/pathreview/commit/5d1ee4ceb81ee16698571db448c00fed9eda3a2e)

**Reproduction summary:**
__[1–2 sentences: How did you reproduce the issue? What did you observe?]__

I went to the file (`pii_scrubber.py`) contacting the root of my chosen issue [#146](https://github.com/ascherj/pathreview/issues/146). I added the code in the `Steps to reproduce` section of my issue and ran the code to reproduce the issue.

I also ran the test file (`tests/unit/test_pii_scrubber.py`) mentioned in my selected issue and confirmed that the relevant tests are failing.

**PLAN.md link:** 
__[link to PLAN.md in your fork]__

[PLAN.md](PLAN.md)

**Walkthrough video (recommended):** 
__[link to your Loom video, ≤2 min — recommended, not graded]__

[walkthrough video](media/issue_walkthrough.mkv)

**Blockers or open questions:**
N/A

## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
Not midweek but here is my progress. Completed the initial failure analysis. By reviewing the failing unit tests in `tests/test_pii_scrubber.py`—specifically `test_us_phone_formats` and `test_detect_phone_pii`—I identified the specific edge cases and delimiter combinations (such as `+1` country codes and non-standard spacing) that are currently bypassing the regex patterns in `PIIScrubber`.

**Next steps:**
- Draft and test updated pattern expressions for US phone numbers.
- Run `pytest` to confirm all previously failing phone redaction and detection tests pass.
- Address applicable linting and pre-commit issues by running `ruff check --fix` and `ruff format` prior to committing.

**Blockers:**
None.

---

### Check-in 2 (end of week)

**PR link:** 

[https://github.com/ascherj/pathreview/pull/559](https://github.com/ascherj/pathreview/pull/559)

**Branch:** fix/146-enhance-pii-scrubber

**What you built:**

The issue is that, in the class `PIIScrubber`, the `scrub` function fails to redact some common phone number patterns, and the `detect` function in the same class cannot detect this PII phone number information in these common patterns either. The root cause of this is likely that the regular expression programmed into the `PII_PATTERNS` constant (below) in the `PIIScrubber` class is inefficient at catching some of the common phone number patterns.

```Python
# current PII_PATTERNS constant in PIIScrubber class used to detect and scrub PII
PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_us": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        "street_address": r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Park|Pl|Plaza|Place|Drive|Dr|Way|Parkway|Pkwy|Point|Pt|Pike|Run|Summit|Summit|Terrace|Ter|Trail|Trl|Tunnel|Turnpike|View|Vista|Vlg|Village|Vly|Valley)",
    }
```

I hypothesized that the root cause of this is likely that the regular expression programmed into the `PII_PATTERNS` constant in the `PIIScrubber` class is inefficient at catching some of the common phone number patterns. To fix this, using the help of Gemini, I improved the US phone pattern to handle spaces, dashes, dots, and optional +1 country code. I also improved international phone pattern to handle spaces between blocks of digits.

**Tests added or updated:**

The test file relevant to these changes is `tests/test_pii_scrubber.py`.

My code resolved failures in the following existing tests:
- `test_us_phone_number_redaction`: 
    - Covers verifying that standard US phone numbers formatted with parentheses and dashes (e.g., `(555) 123-4567`) are correctly redacted to `[REDACTED]`.
- `test_us_phone_formats`: 
    - Covers checking that various common US phone number formats—including hyphenated, dot-delimited, space-separated, and country code-prefixed (`+1`) variations—are reliably detected and redacted.
- `test_detect_phone_pii`: 
    - Covers verifying that `detect()` identifies US phone numbers, categorizes them under the `phone_us` PII type, and returns their match metadata.
- `test_phone_at_start_of_text`: 
    - Covers ensuring that boundary anchor matching works correctly when a phone number appears at the very beginning of a string.

I also added a new unit test, `test_phone_number_partially_formatted_redaction`, which covers the edge case where a US phone number uses mixed delimiters (such as combining parentheses with dot separators like `(800).555.0199`) to ensure it is fully detected and redacted.


**Self-review confirmation:** [x] make check passes  [x] make test-unit passes
NOTE: both of these checks pass in relation to my bug fix. There were existing failures for both checks that pre-date my fix. This is documented in my PR.

**Draft PR feedback received from:** @Divergent-Code

## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [x] Yes  [ ] No — still awaiting review

**Summary of feedback:**
The reviewer (@Divergent-Code) tested my PII scrubbing branch locally and verified that the core fix successfully catches partially formatted phone numbers like `(555) 123-4567` while passing the four new test cases. However, they highlighted three technical edge cases and two repository housekeeping issues:
1. **Catastrophic Backtracking:** The inner repeating quantifier in `phone_intl` (`\+[0-9]{1,3}(?:[-.\s]?[0-9]{1,14})+\b`) causes exponential execution time on long numeric strings ending in a letter (e.g., matching took 95.9s on 30 digits). They suggested using `\+[0-9](?:[-.\s]?[0-9]){7,14}\b` to consume one digit per repetition without backtracking.
2. **Pattern Ordering Regression:** Moving phone patterns above email patterns in `PII_PATTERNS` caused email local parts ending in 10 digits after a separator (e.g., `john.5551234567@example.com`) to have their numbers redacted first, splitting the string and leaking the remaining domain name.
3. **Line Break Redaction:** Using `\s` allows phone regexes to match across newlines (`555\n123 4567`), which risks over-redaction across lines.
4. **Housekeeping:** Noted that `media/issue_walkthrough.mkv` (4.6 MB) was unignored and would permanently inflate git history, and recommended updating the PR title from the branch slug to match the commit message format.

**How you responded:**
I thanked @Divergent-Code for the thorough local testing and actionable feedback. I refactored the `phone_intl` regular expression to the non-backtracking implementation to eliminate performance degradation on malicious or long string inputs. I also restored the pattern execution order in `PII_PATTERNS` so that email addresses are evaluated before phone numbers, preventing partial email redactions. To ensure this ordering behavior remains intact, I added dedicated unit tests specifically covering emails with numeric local parts. 

Regarding the `\s` newline matching, I intentionally chose to retain it after considering the trade-offs, as over-redaction is preferable to leaking sensitive PII in a scrubber context. Finally, I removed the untracked media file from the branch commit history.

---

### Reflection

**What was harder than you expected?**
The most surprisingly difficult aspect was accounting for regular expression performance and execution order side effects within a PII scrubbing pipeline. I initially assumed that simply crafting a regex to match `(555) 123-4567` was sufficient. I didn't expect that changing the sequence of keys in the `PII_PATTERNS` dictionary would break email scrubbing for addresses like `john.5551234567@example.com`, or that a nested quantifier could trigger catastrophic backtracking on long inputs. Beyond the code itself, navigating advanced git workflows like interactive rebasing to clean up commit messages to meet repository guidelines was far more strict than managing git history on solo projects.

**What did you learn about working in a large codebase?**
Working in a production codebase highlighted the strict architectural constraints designed to preserve maintainability. Unlike solo projects where it is tempting to consolidate utility functions into single files, this codebase required adhering to modular separation so that individual components and regex matchers could be isolated for unit testing. I also gained a deep appreciation for automated production safety nets—such as pre-commit hooks, linters, and `make check` suites—which enforce stylistic and structural standards across contributors before code ever reaches the main branch.

**How did AI tools help — and where did they fall short?**
AI tools were really useful for initially drafting regex patterns to match complex phone formatting and for generating test cases covering unusual delimiting edge cases. However, AI completely fell short in predicting  backtracking performance issues under extreme inputs and failed to anticipate how regex execution order in `PII_PATTERNS` would create subtle regression bugs in surrounding email matchers. Human oversight and manual code execution were required to spot the performance bottleneck and structural logic flaws that AI passed over.

**What would you do differently if you started over?**
If I started over, I would select a more complex issue now that I understand the codebase better. From a process standpoint, I would run performance profiling on new regular expressions from day one and test string interactions against existing patterns prior to opening the PR. I would also establish strict git hygiene earlier in the cycle, ensuring that large media files like `media/issue_walkthrough.mkv` are added to `.gitignore` immediately rather than needing to clean them out of the history during the review phase.

**What are you most proud of from this module?**
I am most proud of my growth in navigating and contributing to a complex, unfamiliar codebase using professional git workflows. Going from having zero context on the project's internal structure to diagnosing regex edge cases, configuring pre-commit hooks, resolving reviewer feedback with regression tests, and executing interactive rebases gave me genuine confidence in my ability to join an existing engineering team and contribute production-ready code.

**What was harder than you expected?**
It was harder to find a solution that would not just fix the problem of common US phone numbers not being caught by the PII scubber but also met the efficient/production quality that my reviewer advised for my regular expression update to the PII Scrubber's `PII_PATTERNS` constant. I also interacted with git in a way that I would not have if I was working on a solo project: for instance, I had to rebase to re-name commits to match the naming convention required by the codebase.

**What did you learn about working in a large codebase?**
The constraints of the architecture of a production codebase- i.e. not putting all funcitonality in one file; codebase being organized into modules so that tests- especially unit tests can be written. The linter and other hooks that are run on a production codebase that would not be in a sloppy/ quickly put together solo project.

**How did AI tools help — and where did they fall short?**
AI was most useful in helping me come up with a regex that would be correct to fix my chosen issue. But human oversight was used to detect that a more efficient solution was needed. AI was also used to help refine and make documentation more cohesive. AI was also helpful with brainstorming for edge cases that needed to be covered for unit cases.

**What would you do differently if you started over?**
If I could start over, I may have picked a harder issue because I am more familiar with the codebase now. I was happy with planning and implementation but now I also know that checking for more than just fixing the issue is required.

**What are you most proud of from this module?**
I'm proud that I was able to walkthrough a large, production-quality codebase that I previously had no understanding of. I am proud of what I have learned about hooks, linters, and git workflows. I am proud that I feel that I have more experience with using git.