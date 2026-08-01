# Solution Plan

**Issue:** [#146 — PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

---

## Understand

**Root cause:** Two independent bugs in the `phone_us` regex inside `PIIScrubber.PII_PATTERNS`.

**Bug 1:** The pattern starts with `\b` (word boundary). A word boundary requires a transition between a word character and a non-word character. The `(` in `(555) 123-4567` is not a word character, so `\b` cannot match before it. The engine then tries anchoring at the first digit, but by then the `(` is already behind the cursor and the pattern fails to consume it correctly.

**Bug 2:** The separator between digit groups is `[-.]?` -- dash or dot only. The format `(555) 123-4567` uses a space between `)` and `123`, so even if the area code matched, the rest of the pattern would fail.

**Secondary bug (found during investigation):** The `street_address` pattern has no word boundary at the end. The suffix `Pl` (short for Place/Plaza) matches inside unrelated words like `applications` (`app` + `Pl` + `ications`), causing false positives.

**Expected behavior:** `scrub("Call me at (555) 123-4567")` returns `"Call me at [REDACTED]"`. `detect("Phone: (555) 123-4567")` returns a list containing a phone detection.

**Actual behavior (before fix):** Both return as if no phone number is present.

---

## Map

All changes live in a single file:

| File | What changes |
|---|---|
| `safety/pii_scrubber.py` | `PII_PATTERNS["phone_us"]` and `PII_PATTERNS["street_address"]` |

No other files require changes. The fix does not touch the `scrub()` or `detect()` methods, only the pattern strings they iterate over.

Related test file (read-only reference, no changes needed):
- `tests/unit/test_pii_scrubber.py` -- four pre-written failing tests that serve as the acceptance criteria

---

## Plan

1. **Confirm reproduction.** Run `pytest tests/unit/test_pii_scrubber.py -v` and observe the four failing tests cited in the issue plus one additional failing test (`test_mixed_pii_and_text`) caused by the street address bug.

2. **Fix `phone_us` boundary.** Replace the leading `\b` with `(?<!\d)` (negative lookbehind: "not preceded by a digit"). This anchors correctly regardless of whether the preceding character is `(`, a space, or start of string.

3. **Fix `phone_us` separator.** Expand `[-.]` to `[-. ]` to include a space. Apply the same expansion to the trailing `\b` → `(?!\d)` for symmetry.

4. **Fix `street_address` false positives.** Append `\b` after the closing `)` of the suffix alternation group. This forces the matched suffix to end at a real word boundary, preventing `Pl` from matching inside `applications`.

5. **Verify.** Run the full unit suite (`pytest tests/unit/test_pii_scrubber.py -v`) and confirm 25/25 pass. Run `make check` to confirm no linting or type errors.

---

## Inputs & outputs

**Input:** Any string passed to `scrub()` or `detect()` -- in practice, resume text extracted from a PDF upload.

**`scrub()` output:** The same string with all matched PII replaced by `[REDACTED]`. A parenthesized phone like `(555) 123-4567` should become `[REDACTED]`.

**`detect()` output:** A list of dicts, each with `type`, `value`, `start`, `end`. A parenthesized phone should appear as `{"type": "phone_us", "value": "(555) 123-4567", "start": ..., "end": ...}`.

---

## Risks & unknowns

- **Space separator false positives:** Adding `[ ]` to the separator could theoretically match a space between unrelated digit sequences. In practice the full pattern (`\d{3}[-. ]?\d{3}[-. ]?\d{4}`) is specific enough -- a random sequence of digits with spaces matching all three groups in a resume is unlikely. The `test_detect_no_false_positives` test guards against this.

- **Street address alternation order:** Python's `re` module uses leftmost-longest matching within an alternation group. `Place` must appear before `Pl` in the list for the longer suffix to win. The existing order already satisfies this, so no reordering is needed.

- **International format overlap:** The `phone_us` and `phone_intl` patterns can both match numbers starting with `+1`. This was true before the fix and is unchanged -- not a regression introduced here.

---

## Edge cases

| Case | Expected behavior |
|---|---|
| `(555) 123-4567` at start of string | Redacted -- no preceding character, `(?<!\d)` passes |
| `(555) 123-4567` at end of string | Redacted -- `(?!\d)` passes at end of string |
| `+1 555 123 4567` (space-separated) | Redacted -- space is now a valid separator |
| Two phone numbers in the same string | Both redacted independently |
| Non-phone digit sequences (e.g., years, zip codes) | Not redacted -- pattern requires exactly 10 digits in the right grouping |
| Street address ending in `Pl` (e.g., "10 Park Pl") | Redacted -- `\b` passes after `Pl` when followed by space or end of string |
| Word containing address suffix (e.g., "applications") | Not redacted -- `\b` fails after `Pl` when followed by `i` |
