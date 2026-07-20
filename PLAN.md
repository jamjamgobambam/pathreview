# Solution plan

**Issue:** PII scrubber does not redact parenthesized US phone numbers — [#146](https://github.com/jamjamgobambam/pathreview/issues/146)

### Understand

The current value of `PIIScrubber.PII_PATTERNS["phone_us"]` in [safety/pii_scrubber.py:15](safety/pii_scrubber.py#L15) is:

```python
r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
```

The expected behavior is for `scrub()` to redact common US phone-number formats, including dashed, dotted, parenthesized, and space-separated numbers with an optional country code. `detect()` should also identify each of these as `phone_us`.

Currently, dashed numbers such as `555-123-4567` and dotted numbers such as `555.123.4567` work correctly. However, `(555) 123-4567` and `+1 555 123 4567` are not matched, meaning they remain visible after `scrub()` and cause `detect()` to return `[]`.

The root cause was confrimed using a standalone `re.search` call against the regex:

1. The separator classes, written as `[-.]?`, only support a dash or period between the area code, prefix, and final four digits. Spaces are not supported. This causes formats containing spaces to fail, including the normal space after the closing parenthesis in `(555) 123-4567` and each separator in `+1 555 123 4567`.

2. Adding whitespace to the separator class reveals another issue. The starting `\b` appears before the optional `\(?`. A word boundary requires a transition between a word and non-word character. Since `(` is a non-word character, `\b` cannot match directly before it when the previous character is also non-word, such as a space. The regex engine instead begins the match at the first `5` in `555`. As a result, the rest of `(555) 123-4567` matches, but the opening parenthesis is not included. In that case, `scrub()` would leave a stray `(` in the output rather than redacting the complete number.

This is therefore not only one missing format. Two issues in the same regex are contributing to the failure: the limited separator class and the placement of `\b` before the optional opening parenthesis.

### Map

The expected file changes are:

* **`safety/pii_scrubber.py`** — update the `phone_us` regex inside `PII_PATTERNS` at [safety/pii_scrubber.py:15](safety/pii_scrubber.py#L15). This is the only production-code change that should be required.

* **`tests/unit/test_pii_scrubber.py`** — remove the `xfail` marker introduced in the reproduction commit for `test_parenthesized_phone_number_reproduction` after the fix causes the test to pass. Also verify that `test_us_phone_number_redaction`, `test_us_phone_formats`, `test_detect_phone_pii`, and `test_phone_at_start_of_text` pass without needing any modificatons.

* No other files use `phone_us`. A repository-wide search for both `PII_PATTERNS` and `phone_us` confirmed that the regex is only accessed through `PIIScrubber.scrub()` and `PIIScrubber.detect()`. Therefore, no callers or other integration points need to be changed.

### Plan

1. Expand the separator classes in the `phone_us` regex from `[-.]?` to a class that also accepts whitespace, such as `[-.\s]?`. This should allow `(555) 123-4567` and `+1 555 123 4567` to match.

2. Correct the anchor issue caused by placing `\b` before the optional opening parenthesis. The regex should include the leading `(` in the match instead of beginning at the first digit. One option is to restructure the optional prefix and place the boundary after the parenthesis handling. Another option is to replace `\b` with a lookaround that supports numbers beginning with `(`. Use the same standalone `re.search` test harness from the root-cause investigation to test every format in `test_us_phone_formats`, as well as the exact examples included in the issue descrption.

3. Remove the `strict=True` `xfail` marker from `test_parenthesized_phone_number_reproduction`. Confirm that the reproduction test and the other four currently failing phone-number tests now pass.

4. Run the complete `tests/unit/test_pii_scrubber.py` test suite. Confirm that the change does not break existing behavior for email addresses, Social Security numbers, international phone numbers, or street addresses. The `phone_intl` regex operates on the same text, so it is important to check whether `+1 555 123 4567` could be matched by both patterns.

5. Run `ruff`, `black`, and `mypy` through `make check`, focusing specifically on `safety/pii_scrubber.py`. The pre-commit hooks currently fail on `tests/unit/test_pii_scrubber.py` because of unrelated existing problems described in the Risks section. The updated production file should still pass all applicable checks.

### Inputs & outputs

* **Input:** unstructured text passed into `PIIScrubber.scrub(text)` or `PIIScrubber.detect(text)` that may include a parenthesized US phone number, such as `"Call me at (555) 123-4567"`.

* **Output from `scrub()`:** the full phone number should be replaced by `[REDACTED]`. No leftover punctuation, such as an unmatched `(`, should remain, and all surrounding non-PII text should stay unchanged.

* **Output from `detect()`:** a dictionary entry in the following form:

```python
{
    "type": "phone_us",
    "value": "(555) 123-4567",
    "start": ...,
    "end": ...
}
```

The `start` and `end` positions should cover the full phone number, including both parenthese.

### Risks & unknowns

* **Duplicate detection between `phone_us` and `phone_intl`:** after whitespace is accepted by the US phone regex, `+1 555 123 4567` may match both patterns because `phone_intl` is defined as `r"\+[0-9]{1,3}[-.]?[0-9]{1,14}"`. Verify that `detect()` does not return the same number twice using two different `type` values. Also confirm that the ordered `re.sub` operations in `scrub()` do not create a partially redacted value that is then incorrectly matched by the next regex.

* **Possible new false positives:** allowing `\s` as a separator could cause unrelated groups of three digits, three digits, and four digits separated by spaces to match. Examples could include version values, identifiers, or numeric table data. Compare behavior before and after the update using inputs similar to those in `test_detect_no_false_positives`.

* **`test_mixed_pii_and_text` is also failing, but for a seperate reason:** the `street_address` suffix alternatives contain the bare suffix `Pl`, representing “Place.” Because the pattern is case-insensitive, it matches the ending of the word `appl(ications)` in the phrase `"5 years developing Python applications"`. This causes the output to become `"[REDACTED]ications"`. This is an existing address-regex bug and is outside the scope of issue #146. It should be documented or filed separately so it is not mistaken for a regression from the phone-number fix.

* **Pre-commit failures in the test file:** `tests/unit/test_pii_scrubber.py` already fails the repository’s local `ruff` and `mypy` pre-commit hooks for reasons unrelated to this issue. All 25 current test functions are missing type annotations, and two contain unused variables. Additionally, `make check` only type-checks `api/`, `core/`, `ingestion/`, `rag/`, `agent/`, and `safety/`; it does not type-check `tests/`. A decision is needed on whether to leave these existing issues unchanged and bypass the hooks for the fix commit, as was done for the reproduction commit, or clean them up in a seperate and clearly scoped commit.

### Edge cases

* `(555) 123-4567` — the exact phone format reported in the issue.

* `Call me at (555) 123-4567 or 555-123-4567` — contains both formats in one string. Both numbers must be fully redacted. This is also the exact reproduction text included in the issue.

* `+1 555 123 4567` and `+1 (555) 123-4567` — country-code formats that combine spaces and parentheses.

* A parenthesized phone number at the beginning of a string, as covered by `test_phone_at_start_of_text`, and at the end of a string, as covered by `test_phone_at_end_of_text`. The updated boundary handling must work at both string edges and in the middle of a sentence.

* Non-PII strings containing parentheses or shorter groups of digits must not match. Examples include `"(see section 3) 45.6789"` and version-like values. Confirm that the regex has not been loosened enough to redact these unrelated strings.

* Idempotency should continue to hold: `scrub(scrub(text))` should produce the same result as `scrub(text)`. This behavior is already tested for email addresses in `test_scrub_idempotent`, but it should also be verified for the corrected phone-number format.
