## Solution plan

**Issue:** 
Title: PII scrubber fails to redact parenthesized US phone numbers #146
Link: https://github.com/ascherj/pathreview/issues/146

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
You can document it like this:

### Root Cause

The primary issue is that the phone number regular expression in `pii_scrubber.py` does not support all common phone number formats. While investigating, I observed that it fails to detect not only the parenthesized US format `(555) 123-4567`, but also the international-style format `+1 555 123 4567`. Since these formats are not matched by the regex, they are neither detected by `detect()` nor redacted by `scrub()`.

### Expected Behavior

`PIIScrubber` should consistently recognize and redact all supported phone number formats, including:

* `555-123-4567`
* `(555) 123-4567`
* `555.123.4567`
* `+1 555 123 4567`

For all of these formats:

* `scrub()` should replace the phone number with `[REDACTED]`.
* `detect()` should return a PII detection containing the phone number, its type, and its position.

### Actual Behavior

During testing, I observed:

* `555-123-4567` is successfully detected and redacted.
* `555.123.4567` is successfully detected and redacted.
* `(555) 123-4567` is **not** detected or redacted.
* `+1 555 123 4567` is also **not** detected or redacted.

As a result, the following tests fail:

* `test_us_phone_number_redaction`
* `test_us_phone_formats`
* `test_detect_phone_pii`
* `test_phone_at_start_of_text`

---

### Additional Observation (Outside the Scope of This Issue)

While running the full test suite with `pytest`, I discovered an unrelated failure in `test_mixed_pii_and_text`.

The test expects the word `"Python"` to remain unchanged after scrubbing, but the actual output is:

```text
I worked at TechCorp for [REDACTED]ications.
```

This indicates that the scrubber is incorrectly redacting part of the word **"applications"**, causing the expected word `"Python"` to no longer appear in the output. This suggests another regex or redaction pattern is overmatching ordinary text and modifying non-PII content.

Since this behavior is unrelated to phone number detection, it appears to be a **separate defect** and is outside the scope of the current issue, which focuses specifically on phone number recognition and redaction.


### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

## Files, Functions, and Modules Involved

### Files Expected to be Touched

#### 1. `safety/pii_scrubber.py` **(Primary implementation file)**

This is the main file containing the `PIIScrubber` implementation and is expected to be modified to fix the phone number detection issue.

The following components are involved:

* `PIIScrubber.PII_PATTERNS` – contains the regular expressions used for PII detection, including the `phone_us` and `phone_intl` patterns.
* `PIIScrubber.scrub()` – applies the regex patterns to redact detected PII.
* `PIIScrubber.detect()` – scans the input text and returns detected PII items with their type and position.

#### 2. `tests/unit/test_pii_scrubber.py`

This file contains the unit tests validating the behavior of `PIIScrubber`.

The relevant tests include:

* `test_us_phone_number_redaction`
* `test_us_phone_formats`
* `test_detect_phone_pii`
* `test_phone_at_start_of_text`

While executing the full test suite, I also observed a separate failure in:

* `test_mixed_pii_and_text`

This appears to be an unrelated issue caused by another regex overmatching non-PII text and is outside the scope of the current phone number detection bug.

### Python Modules Used

* `re` – used for regular expression matching and replacement.
* `structlog` – used for logging detected PII.
* `pytest` – used for executing the unit tests.

---

## What else should you check?

For a bug investigation like this, I would verify the following:

### 1. Is `PII_PATTERNS` used anywhere else?

Search for:

```text
PII_PATTERNS
```

If another file imports or modifies it, include that file.

---

### 2. Is `PIIScrubber` used outside the unit tests?

Search for:

```text
PIIScrubber(
```

or

```text
from safety.pii_scrubber import PIIScrubber
```

This tells you whether any integration tests or application code rely on it.

---

### 3. Check for integration or end-to-end tests

Besides

```text
tests/unit/test_pii_scrubber.py
```

look for:

```text
tests/integration/
tests/e2e/
```

If they contain `PIIScrubber` tests, they should also be considered.

---

### 4. Verify the regex itself

From your code, I already notice two likely issues:

* `phone_us` does not correctly handle spaces after the closing parenthesis, which is why `(555) 123-4567` is not matched.
* `phone_intl` is too restrictive and doesn't support formats like `+1 555 123 4567`, explaining why that format also fails.

These belong in `PII_PATTERNS` and are the likely source of the reported bug.

---

### 5. Investigate the unrelated test failure

The failure in:

```python
test_mixed_pii_and_text
```

where

```text
applications
```

became

```text
[REDACTED]ications
```

suggests another regex (possibly the street address pattern or another broad pattern) is matching ordinary text incorrectly. That should be logged as a **separate issue**, since it is unrelated to phone number detection.

---

Overall, for the current bug, **`safety/pii_scrubber.py`** is the only implementation file I would expect to modify, while **`tests/unit/test_pii_scrubber.py`** is the primary test file used to validate the fix and check for regressions.



### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
Yes. Based on everything you've investigated (the failing tests, the code, and the observed behavior), here's a clear answer.

### Steps to Fix the Issue

1. **Review and update the phone number regex patterns**

   * Analyze the existing `phone_us` and `phone_intl` regular expressions in `PII_PATTERNS`.
   * Modify them to correctly recognize all supported phone number formats, including `(555) 123-4567` and `+1 555 123 4567`, while avoiding unintended matches. This is the pattern I am going to replace with  - r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?|\d{3})(?:[-.\s]?)(?:\d{3})(?:[-.\s]?)(?:\d{4})\b",


2. **Validate the detection logic**

   * Verify that the updated regex patterns work correctly with the `detect()` method.
   * Ensure that detected phone numbers include the correct `type`, `value`, `start`, and `end` fields.

3. **Verify redaction behavior**

   * Confirm that `scrub()` properly replaces all matched phone number formats with `[REDACTED]` without affecting surrounding text.

4. **Run and validate the unit tests**

   * Execute the existing phone-related tests in `tests/unit/test_pii_scrubber.py` to ensure the issue is resolved.
   * Run the full `test_pii_scrubber.py` test suite to verify that the changes do not introduce regressions.

5. **Document unrelated issues separately**

   * The failure observed in `test_mixed_pii_and_text`, where non-PII text (`applications`) is partially redacted, appears to be caused by a different regex overmatching ordinary text.
   * Since this is unrelated to phone number detection, it should be tracked as a separate issue rather than addressed as part of the current fix.

This breaks the work into concrete, logical tasks while clearly distinguishing the primary bug from the unrelated issue you discovered during testing.

### Inputs & outputs
What does your fix take as input? What should it produce or change?

### Input

The fix takes **text containing potential phone numbers** as input through the existing `PIIScrubber` methods:

* `scrub(text: str)` – accepts a string that may contain phone numbers and other PII.
* `detect(text: str)` – accepts a string that may contain phone numbers and returns any detected PII.

The supported phone number formats should include:

* `555-123-4567`
* `(555) 123-4567`
* `555.123.4567`
* `+1 555 123 4567`

**Example Input:**

```text
Call me at (555) 123-4567 or +1 555 123 4567. You can also reach me at 555-123-4567.
```

---

### Expected Output / Changes

The fix should update the phone number detection regex so that all supported phone number formats are correctly recognized.

Specifically:

* **`scrub()`**

  * Replace every supported phone number format with `[REDACTED]`.
  * Preserve all surrounding non-PII text without modification.

**Example:**

Input:

```text
Call me at (555) 123-4567 or +1 555 123 4567.
```

Expected output:

```text
Call me at [REDACTED] or [REDACTED].
```

---

* **`detect()`**

  * Return a detection entry for each phone number found.
  * Each entry should include:

    * `type`
    * `value`
    * `start`
    * `end`

**Example:**

Input:

```text
Phone: (555) 123-4567
```

Expected output (illustrative):

```python
[
    {
        "type": "phone_us",
        "value": "(555) 123-4567",
        "start": 7,
        "end": 21
    }
]
```

---

* **Unit Tests**

  * The existing phone-related unit tests should pass without modification in tests/unit/test_pii_scrubber.py 

---

### Additional Observation

While running the full test suite, I also observed a separate failure in `test_mixed_pii_and_text`, where part of the non-PII word **"applications"** was incorrectly redacted. For example:

**Input:**

```text
I worked at TechCorp for 5 years developing Python applications.
```

**Observed Output:**

```text
I worked at TechCorp for [REDACTED]ications.
```

This indicates that another regex is overmatching ordinary text and incorrectly redacting non-PII content. Since this behavior is unrelated to phone number detection, it should be tracked as a separate issue rather than addressed as part of the current fix.


### Risks & unknowns
What could go wrong? What are you still unsure about?
That's a good direction. This question is about **risks, assumptions, and uncertainties**. Based on your investigation, here's a strong answer:

---

### What Could Go Wrong? What Are You Still Unsure About?

While updating the phone number regex should resolve the reported issue, there are a few potential risks and uncertainties:

* **Additional phone number formats:** There may be other valid phone number formats that are not covered by the current tests, such as numbers with extensions (`555-123-4567 ext. 123`), different separators, or formats without separators. Expanding the regex should be done carefully to avoid missing these or unintentionally matching invalid strings.

* **International phone numbers:** I observed that the current implementation also fails to detect the format `+1 555 123 4567`. I'm also unsure whether phone numbers from other countries (e.g., UK, India, Australia) are expected to be supported. If broader international support is required, the existing `phone_intl` regex may need further enhancement.

* **False positives:** Making the regex more permissive could accidentally match non-phone numeric patterns (e.g., IDs, version numbers, or other formatted numbers), leading to incorrect redaction.

* **Impact on existing functionality:** Any changes to the regex should be validated against the existing unit tests to ensure that email, SSN, address detection, and other supported phone number formats continue to work correctly.

* **Separate regex issue:** While running the full test suite, I found an unrelated failure where part of the non-PII word **"applications"** was incorrectly redacted. This suggests another regex is overmatching ordinary text. Although this appears unrelated to the phone number issue, it indicates there may be additional regex-related defects that should be investigated separately.

* **Performance considerations:** Since `scrub()` and `detect()` apply multiple regular expressions over the input text, significantly increasing the complexity of the phone number regex could have a small impact on performance, especially when processing large documents. The updated pattern should remain efficient while improving coverage.

This answer demonstrates that you've thought not only about fixing the immediate bug but also about broader correctness, regression risk, and maintainability.


### Edge cases
What inputs or states should your fix handle gracefully?
This question is asking what kinds of **inputs or edge cases** your fix should handle correctly without failing or producing incorrect results.

A good answer would be:

---

### What Inputs or States Should Your Fix Handle Gracefully?

The fix should correctly handle a variety of valid and invalid inputs without introducing regressions or false positives. Specifically:

* **Supported US phone number formats**, including:

  * `555-123-4567`
  * `(555) 123-4567`
  * `555.123.4567`
  * `+1 555 123 4567`

* **International phone numbers**, where supported by the existing implementation (e.g., `+44 20 7946 0958`), ensuring they continue to be detected and redacted correctly.

* **Multiple phone numbers in the same input**, ensuring each occurrence is detected and redacted independently.

  **Example:**

  ```text
  Call me at (555) 123-4567 or +1 555 123 4567.
  ```

* **Phone numbers appearing in different positions**, such as:

  * At the beginning of the text
  * In the middle of a sentence
  * At the end of the text
  * Across multiple lines

* **Text containing a mix of PII and non-PII**, ensuring only phone numbers are redacted while ordinary text remains unchanged.

* **Inputs with no phone numbers**, where the original text should be returned unchanged and `detect()` should not report any phone-related PII.

* **Empty or whitespace-only inputs**, ensuring the methods return appropriate results without raising exceptions.

* **Avoid false positives**, ensuring that numeric values such as version numbers, IDs, ZIP codes, or other non-phone numeric patterns are not mistakenly detected as phone numbers.

* **Maintain compatibility with existing PII detection**, ensuring that email addresses, SSNs, street addresses, and other supported PII types continue to function correctly after the phone regex is updated.

This covers both the expected use cases and the important edge cases that a robust fix should handle gracefully.
