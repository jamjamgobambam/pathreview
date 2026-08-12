## Solution plan
**Issue:** Phone number regex in PII scrubber misses parenthesized area codes (https://github.com/ascherj/pathreview/issues/146#issue-4884923027)

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
The root cause is that the regular expression defining US phone numbers in `pii_scrubber.py` only accounts for dashed numerical formats (e.g., `555-123-4567`). It fails to account for formatting where the area code is wrapped in parentheses (e.g., `(555) 123-4567`). The expected behavior is that both formats are identified as PII by `detect()` and successfully masked by `scrub()`, but the actual behavior allows parenthesized formats to pass through completely unredacted.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
*   `safety/pii_scrubber.py` (specifically the regex pattern used for phone number detection)
*   `tests/unit/test_pii_scrubber.py` (to ensure the added test cases for parenthesized formats pass)

### Plan
What are the steps to fix this issue?
Break it into 3-5 concrete sub-tasks.
1. Open `safety/pii_scrubber.py` and locate the existing US phone number regular expression.
2. Modify the regex pattern to make the opening and closing parentheses `()` around the area code optional, as well as handling an optional space after the closing parenthesis. 
3. Run the targeted tests in `tests/unit/test_pii_scrubber.py` to confirm the regex correctly detects and scrubs `(555) 123-4567` without breaking the existing dashed format tests.
4. Run the project's full test and linting suite (`make check && make test-unit`) to guarantee the new regex meets code standards and doesn't introduce regressions.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
*   **Input:** A string of text passed to `scrub()` or `detect()` containing the format `(555) 123-4567`.
*   **Output:** The `scrub()` method should output the string with the number replaced by `[REDACTED]`, and `detect()` should output a list identifying the found phone number PII.

### Risks & unknowns
What could go wrong? What are you still unsure about?
The primary risk when modifying regular expressions is introducing false positives. Making the pattern more permissive might accidentally redact other formatted numbers (like reference tags or mathematical coordinates) if the boundaries aren't strict enough. 

### Edge cases
What inputs or states should your fix handle gracefully?
*   Missing spaces between the area code and the rest of the number (e.g., `(555)123-4567`).
*   Mixed punctuation formats (e.g., `(555)-123-4567`).
*   Multiple occurrences of different phone formats within the exact same text block.