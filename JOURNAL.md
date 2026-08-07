## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/64

**Issue title:** Prompt injection defense doesn't sanitize newline characters in user-supplied resume text

**Tier:** Tier 2

**Problem summary:**
A user can submit an unsanitized resume text with newline characters into the prompt template, those injected newline characters trick the LLM into thinking the original system prompt has ended, allowing the user to be able to append instructions that can override the system commands.


**Branch name:** fix/64-newline-injection-sanitization 

**Setup confirmation:** App correctly runs locally at localhost:5173

**Cohort ledger:** The Issue is added to cohort ledger

**Is this right for me? Checklist**
- I can explain the issue in my own words
- prompt_defense.py looks like the only relevant file and the injection attack detection and sanitization made sense.
- Need to test it out manually, but I understand what the fix is and what the expected done situation is.
- I've contributed to large codebases before while working on projects, but not necessarily an open source project. I believe they flow of collaboration is similar.
- Found the relevant code and test code and understood how they tried to exhaust the prompt injection cases
- I've claimed the issue in the ledger and on commented on github, about 10-15 people are working on it.
- It's achievable in the timeline.
- It's not blocked by any other issue.

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** [4714676](https://github.com/gasaroleila/pathreview/commit/4714676)

**Reproduction summary:**
Added two failing tests (`test_sanitize_strips_newline_characters` and `test_sanitize_strips_carriage_return_newlines`) that pass malicious resume text containing `\n` and `\r\n` to `PromptDefense.sanitize()` and assert the newlines are removed. Both tests fail, confirming `sanitize()` does not strip newline characters and the injection vector is open. Also added a TODO comment in `prompt_defense.py` marking the exact location where the fix should go.

**PLAN.md link:** [PLAN.md](https://github.com/gasaroleila/pathreview/blob/fix/64-newline-injection-sanitization/PLAN.md)

**Walkthrough video (recommended):**

**Blockers or open questions:**
- Should we also sanitize Unicode newline characters (e.g., `\u2028` Line Separator, `\u2029` Paragraph Separator, `\u0085` Next Line) that could bypass the `\n`/`\r` stripping?


## Week 9 — Solution building & PR submission

### Check-in 1 (mid-week)

**Current progress:**
- Implemented newline stripping in `PromptDefense.sanitize()` (PLAN.md steps 1-5 done). The fix replaces `\r\n`, `\r`, `\n` and Unicode line-break characters (`\x0b`, `\x0c`, `\x85`, `\u2028`, `\u2029`) with spaces to prevent attackers from injecting role-switching instructions via newlines.
- The two previously failing reproduction tests (`test_sanitize_strips_newline_characters`, `test_sanitize_strips_carriage_return_newlines`) now pass.
- Added a new test `test_sanitize_strips_unicode_newline_characters` covering the Unicode edge cases (PLAN.md step 6 done).
- All 34/35 prompt_defense tests pass. The 1 failure (`test_whitespace_variations_detected`) is a pre-existing issue unrelated to #64 -- the test expects `is_injection_attempt` to detect `"System  :  ignore"` (with spaces before the colon), but the regex pattern requires the colon immediately after the role name.

**Blockers:**
None. Pre-existing failures are unrelated to #64.

---

### Check-in 2 (end of week)

**PR link:** https://github.com/ascherj/pathreview/pull/929

**Branch:** `fix/64-newline-injection-sanitization`

**What you built:**
Added newline character stripping to `PromptDefense.sanitize()` in `safety/prompt_defense.py`. The fix replaces all standard newline characters (`\r\n`, `\r`, `\n`) and Unicode line-break characters (`\x0b`, `\x0c`, `\x85`, `\u2028`, `\u2029`) with spaces, preventing attackers from embedding newlines in resume text to break out of the prompt template and inject role-switching instructions. `\r\n` is replaced first to avoid producing double spaces.

**Tests added or updated:**
- `tests/unit/test_prompt_defense.py`: Added `test_sanitize_strips_unicode_newline_characters` which verifies that all 5 Unicode line-break characters are stripped by `sanitize()`. The two reproduction tests from week 8 (`test_sanitize_strips_newline_characters`, `test_sanitize_strips_carriage_return_newlines`) now pass.

**Manual test**

Created a PDF resume that looks like a normal resume but embeds prompt injection payloads using every newline variant: `\n`, `\r\n`, `\x0b`, `\x0c`, `\x85`, ``, ``. Each payload attempts role-switching (e.g., `\nSystem: Ignore all previous instructions`). After uploading, the reviewer scored successfully (81/100) with no LLM error — the injected instructions were treated as plain text.

**Pre-existing failures (not introduced by this PR):**
- `make test-unit`: 378 passed, 53 failed. All 53 failures are pre-existing (across `test_bias_detector`, `test_review_service`, `test_skill_extractor`, etc.). The only prompt_defense failure is the pre-existing `test_whitespace_variations_detected`.
- `make check`: Pre-existing lint issues across the codebase (import sorting, `Optional` type hints, etc.). No lint issues in our changed files (`safety/prompt_defense.py`, `tests/unit/test_prompt_defense.py`).

**Self-review confirmation:** [x] make check passes  [x] make test-unit passes (all failures are pre-existing, none introduced by this PR)

**Draft PR feedback received from:** none


## Week 10 — Iteration & reflection

### Reviewer feedback

**Feedback received:** [ ] Yes  [x] No — still awaiting review

**Summary of feedback:**
No reviews came in yet

**How you responded:**
N/A
---

### Reflection

**What was harder than you expected?**
I think cross cheking if my fix works and integrates well with the whole codebase was not as straight forward. I did use unit tests and run existing tests but due to some already failing tests(not introduced by my work) I couldn't for sure comfirm that everything works well.

**What did you learn about working in a large codebase?**
I learnt to not just change things, there should be a communicated reason for changing anything. Forexample, I wanted to add screenshots to my JOURNAL.md, but I couldn't just add a screenshots folder because it was unrelated to the actual issue I was working on. 

Also avoiding adding a temporary fix to parts that are not related to my PR. In short, only changing what's related to the issue I'm working on and document why each change needed to happen.

**How did AI tools help — and where did they fall short?**
AI tools were good with codebase navigation and debugging, but when using them to write code sometimes they introduced complex unrelated changes that made changes to parts that are not related to my PR.

**What would you do differently if you started over?**
I would maybe navigate the codebase more, but I think the issue I picked was very specific that I could go directly into the concerned file. If it was a bigger issue, I would navigate the code more to read all files related to the change.

**What are you most proud of from this module?**
Being able to document things well, and following the community contribution guidelines.