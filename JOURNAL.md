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
