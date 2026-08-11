## Solution plan

**Issue:** PII scrubber fails to redact parenthesized US phone numbers #146 https://github.com/ascherj/pathreview/issues/146

### Understand
The root cause of this issue is in safety/pii_scrubber.py. The "phone_us" pattern in PII_PATTERNS does not properly catch cases that use a parenthesized format of US phone numbers. at present it is capable of reading numbers using formats like 555-123-4567 but not (555) 123-4567. It should be capable of detecting both.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
While the issue is noticable because of a failure of the scrub() and detect() functions, the issue is only with the scrubber regex. I expect that I will not need to make alterations outside of the "phone_us" regex pattern.

### Plan
1. understand the current regex pattern
2. find what is causing the failure
3. alter the pattern to catch the parenthesized format
4. test to ensure the pattern works for parenthesized format and to make sure it still catches all other US phone formats

### Inputs & outputs
What does your fix take as input? What should it produce or change?
The fix should still take strings as input to scan with regex. It needs to be able to determine that US phone numbers are indeed phone numbers for other functions to be able to detect and scrub them.

### Risks & unknowns
What could go wrong? What are you still unsure about?
I am concerned that after altering the pattern I may accidentally cause a different format of phone number to not be caught. I am not particularly experienced with regex so I intend to use online tools to help read and understand what I am working with.
### Edge cases
What inputs or states should your fix handle gracefully?
The fix works only with a regex pattern, so any input other than a US phone number should simply not be caught by the pattern.