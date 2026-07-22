## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/64

**Issue title:** Prompt injection defense doesn't sanitize newline characters in user-supplied resume text

**Tier:** Tier 2

**Problem summary:**
The prompt injection defense in the file safety/prompt_defense.py is supposed to clean user-supplied resume text before it gets passed into the system prompt. Right now it only removes a few specific characters like less-than signs, greater-than signs, and curly braces. It does not catch newline-based patterns such as a line break followed by three dashes, or a line break followed by the word System and a colon. This matters because an adversarial user could put one of these patterns into their resume text and use it to break out of the intended prompt and inject their own instructions to the AI. The sanitizer currently gives a false sense of safety because text that looks cleaned can still carry a working injection. My fix needs to expand the sanitization logic to catch these newline based patterns without accidentally breaking normal resume formatting, since real resumes naturally contain line breaks.

**Branch name:** fix/64-newline-sanitization

**Setup confirmation:** App runs locally at localhost:5173

**Cohort ledger:** Issue added to cohort ledger