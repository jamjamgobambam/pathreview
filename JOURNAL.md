## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/64

**Issue title:** Prompt injection defense doesn't sanitize newline characters in user-supplied resume text

**Tier:** Tier 2

**Problem summary:**
The prompt injection defense in the file safety/prompt_defense.py is supposed to clean user-supplied resume text before it gets passed into the system prompt. Right now it only removes a few specific characters like less-than signs, greater-than signs, and curly braces. It does not catch newline-based patterns such as a line break followed by three dashes, or a line break followed by the word System and a colon. This matters because an adversarial user could put one of these patterns into their resume text and use it to break out of the intended prompt and inject their own instructions to the AI. The sanitizer currently gives a false sense of safety because text that looks cleaned can still carry a working injection. My fix needs to expand the sanitization logic to catch these newline based patterns without accidentally breaking normal resume formatting, since real resumes naturally contain line breaks.

**Checklist reasoning ("Is this right for me?"):**
I can locate the exact file this issue affects: safety/prompt_defense.py, and the issue description names it directly, so there is no ambiguity about where to start. I looked at the existing test file, tests/unit/test_prompt_defense.py, and confirmed it already has passing tests for the detection method is_injection_attempt, but no tests confirming that sanitize actually removes what is detected. This told me the gap is narrow and well defined: detection logic already exists, but the cleaning function does not use it. The fix is contained to a single module and does not require touching the database, the API routes, or the frontend, which fits a Tier 2 issue that requires understanding how modules connect but not a large architectural change. The estimated effort of four to six hours matches what I would expect for adding pattern based sanitization plus new tests. The main scope risk I identified is not being too aggressive with the fix and accidentally stripping legitimate resume formatting, which is something I can test for directly using the existing test suite as a safety net.

**Branch name:** fix/64-newline-sanitization

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger
## Week 8 — Reproduction and solution planning

**Reproduction commit link:** https://github.com/nikki2906/pathreview/commit/74e5b74fda37ba5f34d935fde63bcec3846d086c

**Reproduction summary:**
I added a test showing that calling sanitize on text containing a newline based injection pattern, such as a separator line followed by System colon ignore instructions, returns the text completely unchanged. The is_injection_attempt method still flags the sanitized output as an injection attempt afterward, proving that sanitize does not actually remove what it can detect.

**PLAN.md link:** https://github.com/nikki2906/pathreview/blob/fix/64-newline-sanitization/PLAN.md

**Walkthrough video (recommended):** Not recorded this week.

**Blockers or open questions:**
PromptDefense is not called anywhere in the actual resume processing flow, so fixing sanitize alone does not yet protect real user input end to end. I am not sure if that is in scope for this issue or worth flagging as a separate follow up issue.
