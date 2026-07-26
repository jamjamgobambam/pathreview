## Solution plan

**Issue:** [PII scrubber fails to redact parenthesized US phone numbers
](https://github.com/ascherj/pathreview/issues/146#)

**Link:** https://github.com/ascherj/pathreview/issues/146#

### Understand
What is the root cause of this issue? What behavior is expected vs. actual? Line 15 in pii_scrubber.py is the issue because a space between the parentheses breaks the pattern matching of the numbers that follow, 555) will actually be catched, but it breaks down on the rest: 123-34567/

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch. I expect to edit the regex in pii_scrubber.py.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. Read the pii_scrubber.py code to try to understand the issue.
2. Research or use AI assistance if needed.
3. Write a fix (I think just editing the regex on line 15 of pii_scrubber.py will be the fix)
4. Try failing tests and write new tests. Make sure detect function and scrub function are doing their job.
5. Make sure all tests, integration and unit pass.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
The input is text with phone numbers of the format (555) 123-4567. It should product [REDACTED]
```
'Call me at (555) 123-4567 or 555-123-4567'

Should produce:

'Call me at [REDACTED] or [REDACTED]'
```

And s.detect() should detect the number in it with the regex.

### Risks & unknowns
What could go wrong? What are you still unsure about?
If you adjust the regex incorrectly, you could redact the wrong info. If for some reason, there are lists of numbers like (777) 345 they could get redacted. That seems like an uncommon scenario. I guess I am a little bit unsure about regex; I don't have a deep understanding of it, so I will have to read up.

### Edge cases
What inputs or states should your fix handle gracefully?
(777) 345 might get redacted. We need to make sure numbers in parentheses aren't redacted by accident. (555)-123-4567 doesn't work correctly right no either, this is what happens: ([REDACTED].
