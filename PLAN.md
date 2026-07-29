# Solution plan

**Issue:** [#146 — PII scrubber fails to redact parenthesized US phone numbers](https://github.com/ascherj/pathreview/issues/146)

## Understand

**Expected behavior:** Any common US phone number format in user-submitted text —
`555-123-4567`, `(555) 123-4567`, `555.123.4567`, `+1 555 123 4567` — should be
replaced with `[REDACTED]` by `PIIScrubber.scrub()` and reported by
`PIIScrubber.detect()`.

**Actual behavior:** Only dash- and dot-separated numbers are caught.
`(555) 123-4567` and `+1 555 123 4567` pass through untouched: `scrub()` returns
the text unchanged and `detect()` returns an empty list.

**Root cause:** The `phone_us` pattern in `safety/pii_scrubber.py` (line 15)
*does* allow optional parentheses (`\(?` and `\)?`), so the parens themselves are
not the problem. The problem is the separator character class `[-.]?`, which only
permits a dash or a dot between number groups. In `(555) 123-4567` there is a
**space** after the closing paren, and the space has nowhere to match, so the
whole match fails. The same missing-space handling is why `+1 555 123 4567`
fails. So the precise fix is widening the separator handling, not "adding
parentheses support."

**Reproduction (confirmed locally, 2026-07-28):**

```
$ .venv/bin/python -m pytest tests/unit/test_pii_scrubber.py -v
...
5 failed, 20 passed
```

The four failures named in the issue all reproduce:
`test_us_phone_number_redaction`, `test_us_phone_formats`,
`test_detect_phone_pii`, `test_phone_at_start_of_text`.

**Unexpected fifth failure:** `test_mixed_pii_and_text` also fails, but for an
unrelated reason — the `street_address` pattern (line 18) contains the
abbreviation `Pl` and runs with `re.IGNORECASE`, so it false-positive-matches
"5 years developing Python appl" (a digit + words ending in "pl") and redacts
part of the word "applications". Fixing the phone regex will **not** make this
test pass. *(Decision needed: treat as out of scope for #146 and file/report it
separately, or include it in this fix — see Risks.)*

## Map

- `safety/pii_scrubber.py` — the only file whose behavior changes. Specifically
  the `phone_us` entry in `PII_PATTERNS` (line 15). `scrub()` and `detect()`
  both iterate over the same pattern dict, so one regex change fixes both.
- `tests/unit/test_pii_scrubber.py` — the four failing tests define "done";
  the other 20 passing tests (especially `test_detect_no_false_positives`,
  `test_scrub_idempotent`, `test_international_phone_redaction`) are the
  regression guardrail. May add extra format cases here.
- **Not involved (verified by grep):** `PIIScrubber` is not imported anywhere in
  `api/`, `agent/`, `rag/`, or `ingestion/` — the scrubber currently runs only
  via the unit tests. The fix is therefore fully self-contained; there are no
  runtime call sites that could regress.

## Plan

1. **Write down the target format list before touching the regex.** Enumerate
   the formats the pattern must catch (the four in `test_us_phone_formats`,
   plus `+1 (555) 123-4567` and bare `5551234567`) and the strings it must NOT
   catch (version numbers like `1.2.3` from `test_detect_no_false_positives`,
   SSNs like `123-45-6789` which belong to the `ssn` pattern).
2. **Modify the `phone_us` regex** in `safety/pii_scrubber.py:15` to accept a
   space as a separator alongside dash/dot (e.g. widen `[-.]?` to something like
   `[-.\s]?`), and re-check the word-boundary anchors still behave with the
   parenthesized form (the leading `\b` cannot sit before `(`, since both are
   non-word characters).
3. **Run the four target tests** and iterate on the pattern until they pass:
   `.venv/bin/python -m pytest tests/unit/test_pii_scrubber.py -v`.
4. **Run the full test suite** (`.venv/bin/python -m pytest`) to confirm no
   regressions — in particular that the widened pattern doesn't start eating
   dates, version numbers, or the SSN pattern's matches, and that
   `test_scrub_idempotent` still holds.
5. **Resolve the `test_mixed_pii_and_text` question** (see Risks): either
   document it in the PR as a separate pre-existing bug, or fix the
   `street_address` `Pl` false positive in the same PR if maintainers agree
   it's in scope.

## Inputs & outputs

- **Input:** free-form user text (resume/review content) passed to
  `PIIScrubber.scrub(text: str)` and `PIIScrubber.detect(text: str)`.
- **Output of `scrub()`:** the same text with every US-format phone number —
  now including parenthesized and space-separated forms — replaced by the
  literal `[REDACTED]`.
- **Output of `detect()`:** a `list[dict]` with `type`/`value`/`start`/`end`
  entries that now includes `phone_us` hits for the previously missed formats,
  with `start`/`end` spanning the full formatted number (including the parens).
- **No signature changes:** only the value of `PII_PATTERNS["phone_us"]`
  changes; both public methods keep their current interfaces.

## Risks & unknowns

- **Overlap with `phone_intl` (line 16):** if `phone_us` learns to match
  `+1 555 123 4567`, both patterns may match the same substring. `scrub()` is
  safe (text already replaced by `[REDACTED]` can't re-match), but `detect()`
  iterates patterns independently and could report the same number twice.
  Need to check whether duplicate detections matter to any consumer, or add a
  test pinning the expected behavior.
- **False-positive creep:** allowing spaces as separators makes the pattern
  looser — e.g. could `123 456 7890`-shaped text inside addresses, IDs, or
  tables get redacted? `test_detect_no_false_positives` covers version numbers
  and URLs but not space-separated digit runs; may need a new negative test.
- **Scope of `test_mixed_pii_and_text`:** it fails on the pre-existing
  `street_address` `Pl` false positive, not on phones. Unknown whether the
  maintainers want that fixed here or filed separately — will ask in the issue
  thread / Slack before the PR. Either way the PR description must explain why
  this fifth test was failing at the start.
- **Regex readability:** the one-line pattern is already hard to review; if the
  fix makes it much longer, consider `re.VERBOSE` with comments — but that's a
  style call to keep minimal unless it stays clearly readable.

## Edge cases

- `(555) 123-4567` — paren + space (the headline case from the issue).
- `+1 (555) 123-4567` — country code combined with parens.
- `555 123 4567` / `+1 555 123 4567` — space-only separators.
- `(555)123-4567` — parens with **no** space after, which the current pattern
  handles; must not break.
- Phone number at the very start or end of the text (no leading/trailing
  context for `\b` — covered by `test_phone_at_start_of_text` and
  `test_phone_at_end_of_text`).
- Must **not** match: version strings (`1.2.3`), SSNs (`123-45-6789` — the
  `ssn` pattern owns those), 7-digit fragments inside longer digit runs, and
  already-scrubbed text (`[REDACTED]` must survive a second `scrub()` pass
  unchanged).
