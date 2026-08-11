# Reproduction notes — issue #146

https://github.com/ascherj/pathreview/issues/146

Full local stack (`make setup` / `make run`) isn't up on this machine yet, so
I reproduced this at the unit level instead: `safety/pii_scrubber.py` has no
dependency on Postgres/Redis/the API, it only imports `re` and `structlog`,
so a plain venv with `pytest` + `structlog` is enough to exercise the real
code path.

## Steps

```bash
python3.11 -m venv .venv-repro
.venv-repro/bin/pip install pytest structlog
.venv-repro/bin/pytest tests/unit/test_pii_scrubber.py -v
```

## Observed

5 of 25 tests in that file fail. Four are exactly the ones named in the
issue; the fifth (`test_mixed_pii_and_text`) fails for an unrelated reason —
see note at the bottom.

```
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_us_phone_number_redaction
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_us_phone_formats
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_detect_phone_pii
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_phone_at_start_of_text
FAILED tests/unit/test_pii_scrubber.py::TestPIIScrubber::test_mixed_pii_and_text
5 failed, 20 passed in 0.53s
```

Direct call, matching the repro steps in the issue body:

```python
>>> from safety.pii_scrubber import PIIScrubber
>>> s = PIIScrubber()
>>> s.scrub('Call me at (555) 123-4567 or 555-123-4567')
'Call me at (555) 123-4567 or [REDACTED]'
>>> s.detect('Call me at (555) 123-4567')
[]
```

The dashed number gets caught, the parenthesized one right next to it
doesn't, and `detect()` reports zero PII for a string that is nothing but a
phone number.

## Root cause

`PII_PATTERNS["phone_us"]` is:

```python
r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
```

It opens with `\b`. A `\b` only matches at a boundary between a word
character and a non-word character. When the number starts with `(`, the
character immediately before it (a space, in every real-world case) is also
a non-word character — `(` is non-word too — so there's no boundary there
and `\b` never matches. That's why `(555) 123-4567` is invisible to the
pattern while `555-123-4567` (which starts with a digit, a word character)
matches fine.

## Unrelated failure noticed along the way

`test_mixed_pii_and_text` isn't in the issue's list of related tests, and it
isn't a phone-number problem. The input text contains "developing Python
applications" and the scrubbed output comes back as "developing
[REDACTED]ications" — something is eating "Python applic". Tracing it: the
`street_address` pattern's suffix list includes `Pl` (for "Place") with no
trailing `\b`, so `re.IGNORECASE` lets it match the literal substring "pl"
inside "applications". Combined with the greedy-then-backtracking
`[A-Za-z\s]+` before it and the `\d+` earlier in the same sentence ("5
years..."), the whole address pattern ends up matching across word
boundaries it shouldn't. This looks like a separate, pre-existing bug in
`street_address`, not something introduced by or fixable within the scope of
#146 — flagging it in PLAN.md rather than folding it into this fix.
