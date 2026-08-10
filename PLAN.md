## Solution plan

**Issue:** 

PII scrubber fails to redact parenthesized US phone numbers #146
[https://github.com/ascherj/pathreview/issues/146](https://github.com/ascherj/pathreview/issues/146)

### Understand
__What is the root cause of this issue? What behavior is expected vs. actual?__

The issue is that, in the class `PIIScrubber`, the `scrub` function fails to redact some common phone number patterns, and the `detect` function in the same class cannot detect this PII phone number information in these common patterns either. The root cause of this is likely that the regular expression programmed into the `PII_PATTERNS` constant (below) in the `PIIScrubber` class is inefficient at catching some of the common phone number patterns.

```Python
# current PII_PATTERNS constant in PIIScrubber class used to detect and scrub PII
PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_us": r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b",
        "phone_intl": r"\+[0-9]{1,3}[-.]?[0-9]{1,14}",
        "ssn": r"\b(?!000|666)[0-9]{3}-(?!00)[0-9]{2}-(?!0000)[0-9]{4}\b",
        "street_address": r"\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Park|Pl|Plaza|Place|Drive|Dr|Way|Parkway|Pkwy|Point|Pt|Pike|Run|Summit|Summit|Terrace|Ter|Trail|Trl|Tunnel|Turnpike|View|Vista|Vlg|Village|Vly|Valley)",
    }
```
The expected behavior is that the `scrub` method should redact phone numbers, but right now it is showing the phone numbers as plain text. For example:

```Python
print(s.scrub('Call me at (555) 123-4567 or 555-123-4567'))
# observed: 'Call me at (555) 123-4567 or [REDACTED]'
```

Another expected behavior is that the `detect` method should detect and return the PII, but right now, even with a string containing a phone number in the common format, it is returning an empty list. For example:

```Python
print(s.detect('Call me at (555) 123-4567'))
# observed: []
```

The test functions listed below that are related to this issue should also pass. Right now the tests are failing:

(in `tests/unit/test_pii_scrubber.py`)
- test_us_phone_number_redaction
- test_us_phone_formats
- test_detect_phone_pii
- test_phone_at_start_of_text

### Map
__Which files, functions, or modules are involved?__
***List the specific files you expect to touch.***

- safety (module)
    - `pii_scrubber.py` (file)
        - PIIScrubber (class)
            - scrub (function)
            - detect (function)
- tests.unit (module)
    - `test_pii_scrubber.py` (file)
        - TestPIIScrubber (class)
            - test_us_phone_number_redaction (test function)
            - test_us_phone_formats (test function)
            - test_detect_phone_pii (test function)
            - test_phone_at_start_of_text (test function)

### Plan
__What are the steps to fix this issue?__

__Break it into 3–5 concrete sub-tasks.__

- I will inspect the current regular expression being used in PIIScrubber for vulnerabilities or missing common US phone number patterns.
- I will develop and replace the regular expression.
- I will run the app and follow the steps to reproduce in the issue ticket to see if the bug is no longer reproducible.
- Finally, I will run the tests in test_pii_scrubber.py to confirm that the issue has been resolved.

### Inputs & outputs
__What does your fix take as input? What should it produce or change?__

The fix takes in strings of common US phone numbers that the `PII_PATTERNS` constant of regular expressions does not currently match. For example: `(555) 123-4567`.

When the fix works, for the `scrub` method, it should produce from the following string:

`Call me at (555) 123-4567 or 555-123-4567`

this instead:

`Call me at [REDACTED] or [REDACTED]`

And for the `detect` function, when given the following string:

`Call me at (555) 123-4567`

it should return this array:

`[(555) 123-4567]`


### Risks & unknowns
__What could go wrong? What are you still unsure about?__

What could go wrong is that the regular expression added to the current constant may still not be able to match all common US phone number patterns. The new regular expression is the only thing that I am unsure about at this point.

### Edge cases
__What inputs or states should your fix handle gracefully?__

The inputs and states that the fix should handle gracefully are inputs containing common US numbers. If there is a strange or unexpected phone number pattern in the input string, then this still should not cause a crash. The functions will behave as they do in the current state to return unredacted strings or empty arrays.
