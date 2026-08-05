## Week 7 — Issue selection

**Issue link:** [(https://github.com/ascherj/pathreview/issues/64)]

**Issue title:** [Prompt injection defense doesn't sanitize newline characters in user-supplied resume text]

**Tier:** [ ] Tier 1  [X] Tier 2  [ ] Tier 3

**Problem summary:**
[I'm working on issue #64, a tier 2 bug. The bug allows newline sequences to remove the original system prompt and add new instructions. Resolving this issue would prevent adversarial users from inserting new commands and ensure the resume is parsed as data. As this is located in the safety/prompt_defense, it would also preserve the integrity and authority of the original system prompt.]

**Branch name:** [(https://github.com/Ungadeu/pathreview/tree/fix/64-prompt-injection-defense)]

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger


## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [https://github.com/Ungadeu/pathreview/commit/YOUR-COMMIT-HASH-HERE]

**Reproduction summary:**
I reproduced the issue by writing a failing unit test (`test_sanitize_removes_newline_injections`) inside `tests/unit/test_prompt_defense.py`. I passed a malicious resume string containing `\n---\n` and `\nSystem:` into `PromptDefense.sanitize()` and observed that the dangerous newline markers were completely ignored by the current filter, causing my assertions to fail.

**PLAN.md link:** [https://github.com/Ungadeu/pathreview/blob/fix/64-prompt-injection-defense/PLAN.md]

**Walkthrough video (recommended):** [Link to Loom video, if you made one]

**Blockers or open questions:**
I am currently researching the best regular expression (regex) pattern to ensure I catch variations like `\nSYSTEM:` or `\n --- \n` without accidentally deleting normal resume formatting.


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)
**Current progress:**
I have fully implemented the sanitization fix inside `safety/prompt_defense.py`. Instead of manually trying to replace strings, I leveraged the existing `INJECTION_PATTERNS` regex list and applied `re.sub()` with the `re.IGNORES` flag to strip out `\n---\n` and `\nSystem:` during the `sanitize` method.
**Next steps:**
I am running `make check` and `make test-unit` to verify the fix and prepare my branch for a pull request.
**Blockers:**

---

### Check-in 2 (end of week)
**PR link:** [\[PR LINK HERE\]](https://github.com/ascherj/pathreview/pull/243)
**Branch:** `fix/64-prompt-injection-defense`
**What you built:**
I updated the `PromptDefense.sanitize()` method to utilize regular expressions. It now iterates through the class's predefined `INJECTION_PATTERNS` and neutralizes structural role-playing markers and newline injections by substituting them out of the user's data payload.
**Tests added or updated:**
I updated `tests/unit/test_prompt_defense.py` by adding `test_sanitize_removes_newline_injections`, which asserts that malicious sequences are successfully stripped from the final parsed text. 
**Self-review confirmation:** [X] make check passes  [X] make test-unit passes
**Draft PR feedback received from:** none