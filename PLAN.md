# Solution plan

**Issue:** [#111 — No property-based tests for the PII scrubber](https://github.com/ascherj/pathreview/issues/111)
**Tier:** 2 (est. 4–6 hours) · **Branch:** `test/111-pii-scrubber-property-tests`

---

## Understand

### What the issue asks for

`safety/pii_scrubber.py` redacts PII — emails, US and international phone
numbers, SSNs, street addresses — by running five regexes and replacing matches
with `[REDACTED]`. Its only coverage is `tests/unit/test_pii_scrubber.py`: 25
example-based tests built from a fixed list of hand-picked strings.

That has a structural blind spot. **The tests can only ever check formats the
author already thought of.** Any valid PII format outside that list is untested,
and in a safety component an untested format is a potential leak of real user
data into LLM prompts and logs. The issue asks for property-based tests using
`hypothesis`: generate randomized-but-valid PII and assert an invariant — the
raw value never survives `scrub()`.

### Root cause

The gap is not hypothetical. On a clean checkout, **the existing example suite is
already failing**:

```
$ .venv/bin/python -m pytest tests/unit/test_pii_scrubber.py -q
5 failed, 20 passed in 0.62s

FAILED test_us_phone_number_redaction  - assert '[REDACTED]' in 'Call me at (555) 123-4567'
FAILED test_us_phone_formats           - assert '[REDACTED]' in 'Contact: (555) 123-4567'
FAILED test_detect_phone_pii           - assert 0 > 0
FAILED test_phone_at_start_of_text     - assert '[REDACTED]' in '(555) 123-4567 is my phone number.'
FAILED test_mixed_pii_and_text         - assert 'Python' in '...for [REDACTED]ications...'
```

There are two distinct defects behind those failures.

**Defect 1 — phone separator classes omit whitespace.**
[`pii_scrubber.py:15-16`](safety/pii_scrubber.py#L15-L16). `phone_us` separates
digit groups with `[-.]?`; `phone_intl` uses `[-.]?` after the country code.
Neither includes a space, so every space-separated number — the dominant written
form — fails to match. `phone_intl` is *worse than a miss*: it consumes only the
country code and leaves the subscriber number in output that looks scrubbed.

**Defect 2 — `re.IGNORECASE` makes address abbreviations match inside words.**
[`pii_scrubber.py:33`](safety/pii_scrubber.py#L33) applies `re.IGNORECASE` to
every pattern, and the `street_address` alternation contains two-letter
abbreviations (`St`, `Dr`, `Pl`, `Ct`, `Ln`, `Pt`). Lowercased, `Pl` matches
inside "ap**pl**ications" and `Dr` inside "a**dr**". Combined with the unanchored
`[A-Za-z\s]+`, a digit followed by prose gets swallowed.

### Expected vs. actual

| Input | Expected | Actual |
|---|---|---|
| `(555) 123-4567` | `[REDACTED]` | `(555) 123-4567` — untouched |
| `555 123 4567` | `[REDACTED]` | `555 123 4567` — untouched |
| `+1 555 123 4567` | `[REDACTED]` | `+1 555 123 4567` — untouched |
| `+44 20 7946 0958` | `[REDACTED]` | `[REDACTED] 20 7946 0958` — **leaks subscriber number** |
| `123 45 6789` (SSN) | `[REDACTED]` | `123 45 6789` — untouched |
| `123456789` (SSN) | `[REDACTED]` | `123456789` — untouched |
| `5 years developing Python applications` | unchanged | `[REDACTED]ications` — **false positive** |
| `Version 2 Dr Smith reviewed it` | unchanged | `Version [REDACTED]ed it` — **false positive** |

### Property-based reproduction

The issue's real point is that properties find these *automatically*. A harness
with a strategy per PII type and the invariant "generated value never survives
`scrub()`" fails 3 of 4 properties, and hypothesis shrinks each to a minimal
counterexample:

| Property | Result | Shrunk counterexample |
|---|---|---|
| US phone never survives | ❌ FAIL | `000-000 0000` |
| Intl phone never leaks a digit group | ❌ FAIL | `+1 00 000` → leaks `000` |
| Prose is not redacted (no false positives) | ❌ FAIL | `I worked for 5 adr` |
| Email never survives | ✅ PASS (200 examples) | — |

The email property passing is a deliberate control: it shows the properties fail
on real defects rather than on everything.

---

## Map

### Files I will touch

| File | Change | Status |
|---|---|---|
| `tests/unit/test_pii_scrubber_repro_111.py` | **New.** Reproduction — strategies + failing properties, `xfail(strict=True)` | ✅ committed |
| `PLAN.md` | **New.** This document | ✅ committed |
| `JOURNAL.md` | Week 8 entry | ✅ committed |
| `tests/unit/test_pii_scrubber_properties.py` | **New.** The deliverable suite — full strategies, round-trip + cross-API properties | ⬜ Week 9 |
| `.gitignore` | One line for the gitignored video script | ✅ committed |

### Files I will read but *not* modify

| File | Why |
|---|---|
| [`safety/pii_scrubber.py`](safety/pii_scrubber.py) | The system under test. `PII_PATTERNS` (L13–19), `scrub()` (L21–35), `detect()` (L37–59). **Behavior change proposed as a follow-up — see Risks.** |
| [`tests/unit/test_pii_scrubber.py`](tests/unit/test_pii_scrubber.py) | Existing 25 example tests. Template for fixture style and marker conventions; 5 of them currently fail. |
| `pyproject.toml` | Confirms `hypothesis>=6.92.0` is already a dev dep (L46) and defines the `unit` marker (L85–90). No change needed. |
| `Makefile` | `test-unit` target runs `pytest tests/unit -v -m unit`; new file must carry the `unit` marker to be picked up. |

### Functions under test

- `PIIScrubber.scrub(text) -> str` — the primary invariant target.
- `PIIScrubber.detect(text) -> list[dict]` — returns `type`/`value`/`start`/`end`;
  offsets are a second, independently checkable property.
- `PIIScrubber.PII_PATTERNS` — the five regexes; each gets its own strategy.

---

## Plan

**Sub-task 1 — Reproduction commit.** ✅ *Done.*
Add `tests/unit/test_pii_scrubber_repro_111.py` pinning the three shrunk
counterexamples as `@example` decorators so failures are deterministic rather
than seed-dependent. Mark defect tests `xfail(strict=True)`.

**Sub-task 2 — Build the full strategy set.**
Write `@st.composite` strategies in `tests/unit/test_pii_scrubber_properties.py`
for all five PII types: `emails()`, `us_phones()`, `intl_phones()`, `ssns()`,
`street_addresses()`. Each parameterizes exactly the dimensions the fixed
examples hold constant — separator character (`-`, `.`, space, none),
parenthesized vs. bare area code, optional `+1`, TLD shape, casing, and for
addresses the full suffix list from `PII_PATTERNS`.

**Sub-task 3 — Write the round-trip properties.**
One per PII type: embed the generated value in surrounding text, assert it does
not appear in `scrub()`'s output. This is the invariant the issue names.

**Sub-task 4 — Write the cross-API and invariant properties.**
- `detect()`/`scrub()` agreement: anything `detect()` reports must be absent
  from `scrub()`'s output.
- Offset correctness: `text[d["start"]:d["end"]] == d["value"]` for every
  detection.
- Idempotence: `scrub(scrub(t)) == scrub(t)`.
- No-PII passthrough: text with no PII is returned unchanged.

**Sub-task 5 — Stabilize and land.**
Register a deterministic hypothesis profile (`max_examples=200`, `deadline=None`)
so CI doesn't flake on timing and the suite stays inside the ~30s budget
documented for `make test-unit`. Run `make test-unit`, `make lint`,
`make typecheck`. Report the 5 pre-existing example-test failures on the issue
thread — they aren't mine, and the maintainer should know `main` is red.

---

## Inputs & outputs

**Input.** Randomized-but-valid PII values produced by hypothesis strategies —
not a fixed list. Each strategy is bounded to formats that are genuinely valid
for that PII type, embedded in surrounding prose so matching is tested in
context rather than against a bare string.

**Output.**
- A new test module, ~8–10 properties plus 5 strategies, wired into `make test-unit`.
- Executable documentation of three defects, each pinned to a shrunk counterexample.
- A green suite: known defects are held by `xfail(strict=True)`, so CI passes
  today and fails loudly the moment the regexes are fixed and the markers go stale.

**Explicitly not produced (this PR).** Any change to `safety/pii_scrubber.py`.
The issue asks for tests; rewriting regexes in a safety component is a behavior
change deserving its own issue and review. The fix is drafted below so the
maintainer can pull it forward if they prefer one PR.

<details>
<summary>Drafted regex fix, if the maintainer wants it in scope</summary>

- `phone_us`: replace `[-.]?` with `[-.\s]?`, and allow `\)?\s*` after the area code.
- `phone_intl`: replace `[-.]?[0-9]{1,14}` with a repeated group that permits
  spaces, so the whole number is consumed instead of just the country code.
- `street_address`: compile without `re.IGNORECASE` (or drop the flag for this
  pattern only), anchor the suffix with a trailing `\b`, and bound the
  `[A-Za-z\s]+` run to a small word count.
- `ssn`: allow space-separated and unseparated forms.

Each as its own commit, so the test-only change stays reviewable independently.
</details>

---

## Risks & unknowns

| Risk | Where it bites | Mitigation |
|---|---|---|
| **Scope disagreement.** Maintainer may expect the regex fix in this PR, not a follow-up. | `safety/pii_scrubber.py` untouched by my PR | **Open question — asking on issue #111 before I open the PR.** Fix is pre-drafted above so pivoting costs one commit, not a redesign. |
| **`xfail(strict=True)` blocks CI** if someone fixes the regexes without unmarking. | `test_pii_scrubber_repro_111.py` | That's the intended signal — `strict` fails loudly on unexpected pass, and each marker carries a `reason` with the issue link. |
| **Flaky xfail.** A property that only *sometimes* finds its counterexample would flip between xfail and xpass, breaking `strict`. | The prose false-positive property especially — it depends on hypothesis generating a substring like `dr`/`pl`. | **Already handled:** every failing property carries a pinned `@example` with the shrunk counterexample, so failure is deterministic. Verified: 6 xfailed, 0 unexpected, across repeated runs. |
| **Strategies generate invalid PII**, producing bogus failures that waste maintainer review. | All five strategies | Constrain each strategy to documented formats; add a self-test asserting generated values match a reference validator before asserting anything about the scrubber. |
| **Property tests slow the "fast" unit suite** (`make test-unit` is documented at ~30s). | `Makefile` target | Cap `max_examples=200`, set `deadline=None`, measure runtime before/after. Current repro file runs in 0.27s. |
| **The wider unit suite is broadly red** — 53 pre-existing failures across `skill_extractor`, `tech_detector`, `security`, `structural_chunker`. | Whole repo | Verified identical count with and without my file, so none are mine. Risk is that a grader or maintainer reads the red suite as my doing — flagging explicitly in the PR description. |

**Unknowns going into Week 9**

1. Does the maintainer want the regex fix in this PR? *(blocking the PR shape, not the test work)*
2. Should SSN space/unseparated forms count as in-scope PII, or is dashed-only intentional? The regex has deliberate exclusions (`(?!000|666)`) suggesting real thought went in, so I don't want to assume the omission is a bug.
3. Is there a project convention for hypothesis profiles? No existing `conftest.py` registration — I'll propose one rather than assume.

---

## Edge cases

The properties must handle these gracefully — several are already covered by the
existing example suite and must not regress.

**Must stay redacted (true positives)**
- Phone separator variants: `-`, `.`, space, none, and *mixed* within one number (`000-000 0000` — the shrunk counterexample).
- Parenthesized area codes, with and without a following space.
- Optional `+1` country prefix; international `+CC` with 2–4 digit groups.
- PII at the very start and very end of a string (boundary/`\b` behavior).
- Multiple PII items of the same and different types in one string.
- Mixed case (`John.Doe@Example.COM`).
- RFC-valid but unusual emails: `+tag`, `_`, `%`, subdomains, multi-part TLDs (`.co.uk`).

**Must stay untouched (false positives)**
- Prose containing an address abbreviation as a substring: `applications` (`pl`), `adr` (`dr`), `street` inside `streetwise`.
- Version numbers — `1.2.3` must not read as an SSN.
- URLs — `https://example.com` must not read as an email.
- A bare digit followed by ordinary words: `5 years`, `3 valleys`, `4 pt increase`.

**Degenerate inputs**
- Empty string, whitespace-only, very long strings.
- Text with no PII at all — must be returned byte-identical.
- Already-scrubbed text — `scrub()` must be idempotent, and `[REDACTED]` must not itself be re-matched.

**`detect()`-specific**
- Empty input returns `[]`, not `None`.
- Offsets must slice back to the reported `value` even with overlapping matches
  from different patterns (e.g. a phone number inside a longer digit run).
