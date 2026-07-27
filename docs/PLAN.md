## Solution plan

**Issue:** [#64 Prompt injection defense doesn't sanitize newline characters in user-supplied resume text](https://github.com/ascherj/pathreview/issues/64)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
The root cause is that the sanitization logic in `safety/prompt_defense.py` is currently designed to strip template symbols (like `<, >, {`) but does not account for newline-based role-switching markers. Actual behavior: adversarial markers like `\n---\n` and `\nSystem:` are left intact, allowing prompt injection. Expected behavior: the sanitizer should strip or neutralize these specific newline sequences so the LLM parses the resume strictly as data.

### Map
Which files, functions, or modules are involved?
* `safety/prompt_defense.py` (specifically the `sanitize` function within the `PromptDefense` class)
* `tests/unit/test_prompt_defense.py` (where the new failing test was added and will be verified)

### Plan
What are the steps to fix this issue?
1. Locate the `sanitize` function in `safety/prompt_defense.py`.
2. Implement regular expressions (`re.sub`) or string replacement logic to target `\n---\n` (and its length variations) as well as `\nSystem:` (and other role-playing keywords like `\nUser:` or `\nAssistant:`).
3. Ensure the replacement logic substitutes these markers with a safe space or simply strips them without destroying surrounding text.
4. Run `make test-unit` to confirm the failing `test_sanitize_removes_newline_injections` now passes.
5. Verify no existing tests were broken by the new logic.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
* **Input:** A raw string of user-supplied resume text that may contain malicious structural markers.
* **Output:** A sanitized string where the dangerous newline boundaries have been removed or neutralized, preserving the rest of the legitimate resume content.

### Risks & unknowns
What could go wrong? What are you still unsure about?
The primary risk is being too aggressive with the sanitization. For example, if a user legitimately uses hyphens for a bulleted list or writes the word "System" at the start of a new line (e.g., "Systems Administrator"), a poorly written regex might accidentally delete their valid resume experience. 

### Edge cases
What inputs or states should your fix handle gracefully?
* Case insensitivity (e.g., `\nSYSTEM:` vs `\nSystem:`).
* Whitespace variations (e.g., `\n   ---   \n` or `\n System :`).
* Multiple injection attempts within the same document.
* Legitimate newlines that should *not* be removed.