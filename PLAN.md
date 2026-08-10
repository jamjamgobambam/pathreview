## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

### Understand
<!-- What is the root cause of this issue? What behavior is expected vs. actual? -->
There is a pattern matching error in `pii_scrubber.py`. It cannot match with phone numbers using parentesis, such as `(123) 456-7890`. This issue causes scrub() and detect() to fail identifying these types phone numbers. 

### Map
`pii_scrubber.py`

### Plan
<!-- What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks. -->
1. Modify the `street_address` value to add word boundaries to its suffix list and make the middle `[A-Za-z\s]+` non-greedy or bounded.
2. Modify the `phone_us` value to match US phone numbers with parenthesis.
3. Rerun the tests in `test_pii_scrubber.py` to confirm the issue has been resulved.

### Inputs & outputs
<!-- What does your fix take as input? What should it produce or change? -->
Input: "My number is (555) 586-3987."
Output: "My number is [REDACTED]."

### Risks & unknowns
<!-- What could go wrong? What are you still unsure about? -->
Modifying the pattern matching code cause the functions to identigy false positives or negatives, causing them to under- or over-match under certain conditions.

### Edge cases
<!-- What inputs or states should your fix handle gracefully? -->
- Numbers with 10 digits: 1235554567
- International numbers that share US format: +1 (555) 123-4567
- Text with mupltiple overlapping PII types: john@example.com123-456-7890