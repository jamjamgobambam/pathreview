## Solution plan

**Issue:**  #146 PII scrubber fails to redact parenthesized US phone numbers

**Issue Link** https://github.com/ascherj/pathreview/issues/146

### Understand
**What is the root cause of this issue? What behavior is expected vs. actual?**

The root cause is a \b (word boundary) in the regex. A word boundary just checks that a letter or digit sits right next to a space or punctuation, which is how the regex makes sure it matches a whole number instead of part of one. The problem is that ( and the space before it are both non word characters, so there's no boundary there at all, and the regex never starts matching. This is why 555-123-4567 gets caught correctly but (555) 123-4567 slips through untouched in both scrub() and detect(). The fix checks whether a digit comes right before or after the match instead of checking for a word boundary, so a leading ( no longer blocks it and both formats get caught. After the fix, scrub() should redact (555) 123-4567 the same way it already redacts 555-123-4567, and detect() should return a matching entry for it instead of an empty list."


### Map
**Which files, functions, or modules are involved?
List the specific files you expect to touch.**

* **src/safety/pii_scrubber.py:** contains the phone_us regex in the PII_PATTERNS dictionary, which is the actual line that needs to be fixed.

* **tests/unit/test_pii_scrubber.py:** contains the four currently-failing tests (test_us_phone_number_redaction, test_us_phone_formats, test_detect_phone_pii, test_phone_at_start_of_text) that should pass once the fix is applied, plus test_detect_no_false_positives, which I'll re-run to confirm the fix doesn't introduce any new false matches.

### Plan
**What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.**

**1. Update the phone_us regex:** In src/safety/pii_scrubber.py: replace the leading and trailing \b word boundaries with digit-based lookarounds ((?<!\d) and (?!\d)), and allow whitespace as a valid separator alongside - and ..

**2. Re-run the existing test suite:** In tests/unit/test_pii_scrubber.py to confirm the four previously-failing tests now pass, and that test_detect_no_false_positives still passes with no new false matches.

**3. Add a new test case:** Cover the parenthesized format explicitly (if not already fully covered), to guard against this regression happening again in the future.

**4. Manually verify with a quick script:** that both scrub() and detect() correctly handle (555) 123-4567, 555-123-4567, and a few edge cases like phone numbers at the very start or end of a string.

**5. Commit the fix:** Commit with a clear message referencing the issue number, and push it to the branch for review.

### Inputs & outputs
**What does your fix take as input? What should it produce or change?**
The fix takes a text string as input, the same as before, passed into either scrub() or detect(). scrub() should return the text with any phone number (including the parenthesized format) replaced by [REDACTED], while detect() should return a list of dictionaries flagging that phone number's type, value, and position. The only thing that changes is the phone_us pattern inside pii_scrubber.py — no other files, function signatures, or return formats are affected.

### Risks & unknowns
**What could go wrong? What are you still unsure about?**
The biggest risk is that loosening the rule could make the regex too broad and start flagging things that aren't phone numbers, like version numbers or dates, so the false-positive test needs close attention. Allowing spaces as separators could also accidentally join two unrelated numbers sitting near each other in a sentence. It's still unclear whether this same regex is used anywhere else in the codebase besides pii_scrubber.py, so that's worth checking before finishing the fix.

### Edge cases
**What inputs or states should your fix handle gracefully?**
The fix should handle all four common US phone formats correctly: dashed (555-123-4567), dotted (555.123.4567), parenthesized ((555) 123-4567), and with a country code (+1 555 123 4567). It should also work regardless of where the phone number sits in the text, whether at the very start, the very end, or in the middle of a sentence. Finally, it needs to keep ignoring unrelated digit sequences, like version numbers or short numeric codes, so it doesn't introduce new false positives while fixing the original bug.