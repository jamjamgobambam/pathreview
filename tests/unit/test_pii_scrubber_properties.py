"""Property-based tests for the PII scrubber (issue #111).

https://github.com/ascherj/pathreview/issues/111

``tests/unit/test_pii_scrubber.py`` covers ``PIIScrubber`` with a fixed list of
hand-picked strings. That has a structural blind spot: the tests can only ever
check formats the author already thought of, and in a safety component an
untested format is a potential leak of real user data into LLM prompts and logs.

This module closes that gap with ``hypothesis``. Each PII type gets a strategy
that generates randomized-but-valid values, parameterizing exactly the
dimensions the fixed examples hold constant -- separator character,
parenthesized vs. bare area code, optional country prefix, TLD shape, casing.
The central invariant is the one the issue names:

    a generated PII value never survives ``scrub()``

Alongside the round-trip properties are cross-API properties (``detect()`` and
``scrub()`` must agree, reported offsets must slice back to the reported value)
and negative properties (ordinary prose must come back byte-identical), so a
scrubber that redacted everything would not pass either.

These properties are what found the three defects fixed in this PR; see
``test_pii_scrubber_regression_111.py`` for the shrunk counterexamples pinned as
regression tests.
"""

import re
import string

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from safety.pii_scrubber import STREET_SUFFIXES, PIIScrubber

pytestmark = pytest.mark.unit

# `make test-unit` is documented at ~30s, so the properties are capped rather
# than left at hypothesis' defaults. `deadline=None` because the first example
# pays one-time regex compilation and would otherwise flake in CI.
#
# Applied per test rather than registered as a global profile in
# `tests/conftest.py`: no hypothesis profile convention exists in this repo yet,
# and this module should not impose one on every other suite.
property_test = settings(max_examples=200, deadline=None)

REDACTED = "[REDACTED]"

DIGITS = "0123456789"
PHONE_SEPARATORS = st.sampled_from(["-", ".", " ", ""])


# `PIIScrubber` is stateless and its patterns are compiled once at import, so a
# single shared instance is safe. A pytest fixture is not usable here: hypothesis
# rejects function-scoped fixtures under `@given`, since they are not reset
# between generated examples.
SCRUBBER = PIIScrubber()


# ---------------------------------------------------------------------------
# Strategies -- randomized but valid PII.
#
# Each strategy is deliberately bounded to formats that are genuinely valid for
# its type. A strategy that emitted malformed values would produce failures
# that say nothing about the scrubber.
# ---------------------------------------------------------------------------


@st.composite
def emails(draw: st.DrawFn) -> str:
    """Valid email addresses, including the RFC-legal but unusual shapes."""
    # Local part: alphanumeric at both ends, `._%+-` permitted in between.
    first = draw(st.sampled_from(string.ascii_letters + string.digits))
    middle = draw(st.text(alphabet=string.ascii_letters + string.digits + "._%+-", max_size=12))
    last = draw(st.sampled_from(string.ascii_letters + string.digits))
    local = f"{first}{middle}{last}"

    # Domain: one or more labels, then a TLD (single- or multi-part).
    labels = draw(
        st.lists(
            st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=8),
            min_size=1,
            max_size=3,
        )
    )
    tld = draw(st.sampled_from(["com", "org", "net", "io", "dev", "co.uk", "com.au"]))
    return f"{local}@{'.'.join(labels)}.{tld}"


@st.composite
def us_phones(draw: st.DrawFn) -> str:
    """US phone numbers across every separator/format variant humans write."""
    area = draw(st.text(alphabet=DIGITS, min_size=3, max_size=3))
    exchange = draw(st.text(alphabet=DIGITS, min_size=3, max_size=3))
    line = draw(st.text(alphabet=DIGITS, min_size=4, max_size=4))

    area_part = f"({area})" if draw(st.booleans()) else area
    sep1 = draw(PHONE_SEPARATORS)
    sep2 = draw(PHONE_SEPARATORS)

    prefix = draw(st.sampled_from(["", "1", "+1"]))
    if prefix:
        prefix += draw(st.sampled_from(["-", ".", " ", ""]))

    return f"{prefix}{area_part}{sep1}{exchange}{sep2}{line}"


@st.composite
def intl_phones(draw: st.DrawFn) -> str:
    """International numbers written the way humans write them: +CC then groups."""
    country = draw(st.integers(min_value=1, max_value=998))
    groups = draw(
        st.lists(
            st.text(alphabet=DIGITS, min_size=2, max_size=4),
            min_size=2,
            max_size=4,
        )
    )
    separator = draw(st.sampled_from(["-", ".", " "]))
    return f"+{country}{separator}{separator.join(groups)}"


@st.composite
def ssns(draw: st.DrawFn) -> str:
    """SSNs in the two separated forms, honouring the pattern's own exclusions."""
    area = draw(
        st.text(alphabet=DIGITS, min_size=3, max_size=3).filter(lambda a: a not in ("000", "666"))
    )
    group = draw(st.text(alphabet=DIGITS, min_size=2, max_size=2).filter(lambda g: g != "00"))
    serial = draw(st.text(alphabet=DIGITS, min_size=4, max_size=4).filter(lambda s: s != "0000"))
    separator = draw(st.sampled_from(["-", " "]))
    return f"{area}{separator}{group}{separator}{serial}"


# Addresses are generated from the same suffix list the pattern is built from,
# so the strategy cannot silently drift away from the implementation.
NAME_WORDS = st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10).map(str.capitalize)


@st.composite
def street_addresses(draw: st.DrawFn) -> str:
    """House number, one to four capitalized name words, a recognised suffix."""
    number = draw(st.integers(min_value=1, max_value=99999))
    names = draw(st.lists(NAME_WORDS, min_size=1, max_size=4))
    suffix = draw(st.sampled_from(STREET_SUFFIXES))
    return f"{number} {' '.join(names)} {suffix}"


# Ordinary prose, guaranteed PII-free. Drawn from real words rather than random
# letters so a failure reads like something a user would actually have written.
PROSE_WORDS = [
    "years",
    "developing",
    "python",
    "applications",
    "and",
    "kubernetes",
    "deployment",
    "streetwise",
    "address",
    "adr",
    "place",
    "drive",
    "court",
    "the",
    "project",
    "uses",
    "a",
    "modern",
    "stack",
    "with",
    "strong",
]
prose = st.lists(st.sampled_from(PROSE_WORDS), min_size=1, max_size=12).map(" ".join)


# ---------------------------------------------------------------------------
# Round-trip properties -- the invariant issue #111 asks for.
# ---------------------------------------------------------------------------


@property_test
@given(email=emails())
def test_email_never_survives_scrub(email: str) -> None:
    """INVARIANT: a generated email never appears in scrub() output."""
    scrubbed = SCRUBBER.scrub(f"Contact me at {email} for more info.")

    assert email not in scrubbed
    assert REDACTED in scrubbed


@property_test
@given(phone=us_phones())
def test_us_phone_never_survives_scrub(phone: str) -> None:
    """INVARIANT: a generated US phone number never appears in scrub() output."""
    scrubbed = SCRUBBER.scrub(f"Call me at {phone} today")

    assert phone not in scrubbed
    assert REDACTED in scrubbed


@property_test
@given(phone=intl_phones())
def test_intl_phone_never_leaks_a_digit_group(phone: str) -> None:
    """INVARIANT: no part of an international number survives scrub().

    Partial redaction is the failure mode this property exists to catch: output
    that contains ``[REDACTED]`` looks safe to a reviewer even when the
    subscriber number is sitting right next to it.
    """
    scrubbed = SCRUBBER.scrub(f"Reach me at {phone}")

    assert phone not in scrubbed
    leaked = [group for group in re.findall(r"\d+", phone) if group in scrubbed]
    assert not leaked, f"leaked {leaked} in {scrubbed!r}"


@property_test
@given(ssn=ssns())
def test_ssn_never_survives_scrub(ssn: str) -> None:
    """INVARIANT: a generated SSN never appears in scrub() output."""
    scrubbed = SCRUBBER.scrub(f"SSN: {ssn}")

    assert ssn not in scrubbed
    assert REDACTED in scrubbed


@property_test
@given(address=street_addresses())
def test_street_address_never_survives_scrub(address: str) -> None:
    """INVARIANT: a generated street address never appears in scrub() output."""
    scrubbed = SCRUBBER.scrub(f"Address: {address}, Apt 4")

    assert address not in scrubbed
    assert REDACTED in scrubbed


@property_test
@given(
    email=emails(),
    phone=us_phones(),
    ssn=ssns(),
    address=street_addresses(),
)
def test_no_pii_survives_when_all_types_appear_together(
    email: str,
    phone: str,
    ssn: str,
    address: str,
) -> None:
    """INVARIANT: patterns do not interfere when several PII types share a string.

    ``scrub()`` applies its patterns in sequence to progressively rewritten
    text, so a match consumed by an earlier pattern can change what a later one
    sees. This checks that composition does not open a hole.
    """
    text = f"{email} lives at {address}, phone {phone}, SSN {ssn}."
    scrubbed = SCRUBBER.scrub(text)

    for value in (email, phone, ssn, address):
        assert value not in scrubbed


# ---------------------------------------------------------------------------
# Negative properties -- a scrubber that redacted everything must not pass.
# ---------------------------------------------------------------------------


@property_test
@given(text=prose)
def test_prose_without_pii_is_returned_unchanged(text: str) -> None:
    """INVARIANT: text containing no PII comes back byte-identical."""
    assert SCRUBBER.scrub(text) == text


@property_test
@given(text=prose)
def test_digit_followed_by_prose_is_not_an_address(text: str) -> None:
    """INVARIANT: a bare number followed by ordinary words is not PII.

    This is the false-positive family that swallowed "5 years developing Python
    applications" -- lowercased, the two-letter street abbreviations match
    inside ordinary words.
    """
    sentence = f"I worked there for 5 {text}"

    assert SCRUBBER.scrub(sentence) == sentence


@pytest.mark.parametrize(
    "text",
    [
        "The project uses version 1.2.3 in production.",
        "Available at https://example.com/docs",
        "Increase of 4 pt across 3 valleys",
        "He is streetwise and drives a car",
        "Temperature rose +12 degrees overnight",
        "Order 123456789 shipped on time",
    ],
)
def test_known_non_pii_is_not_redacted(text: str) -> None:
    """Concrete near-misses that must not trip any pattern."""
    assert SCRUBBER.scrub(text) == text


# ---------------------------------------------------------------------------
# Cross-API and structural properties.
# ---------------------------------------------------------------------------


@property_test
@given(email=emails(), phone=us_phones(), ssn=ssns())
def test_detect_and_scrub_agree(email: str, phone: str, ssn: str) -> None:
    """INVARIANT: anything detect() reports is absent from scrub() output.

    The two methods share a pattern set, so a disagreement means one of them is
    lying about what it handles.
    """
    text = f"Email {email}, phone {phone}, SSN {ssn}."
    scrubbed = SCRUBBER.scrub(text)

    for detection in SCRUBBER.detect(text):
        assert detection["value"] not in scrubbed


@property_test
@given(email=emails(), phone=us_phones(), ssn=ssns())
def test_detect_offsets_slice_back_to_the_reported_value(email: str, phone: str, ssn: str) -> None:
    """INVARIANT: text[start:end] == value for every detection."""
    text = f"Email {email}, phone {phone}, SSN {ssn}."

    for detection in SCRUBBER.detect(text):
        assert text[detection["start"] : detection["end"]] == detection["value"]


@property_test
@given(email=emails(), phone=us_phones(), ssn=ssns(), address=street_addresses())
def test_scrub_is_idempotent(email: str, phone: str, ssn: str, address: str) -> None:
    """INVARIANT: scrub(scrub(t)) == scrub(t).

    A second pass must be a no-op -- in particular the ``[REDACTED]`` marker
    itself must never be re-matched, and redaction must not splice neighbouring
    text into something that newly looks like PII.
    """
    text = f"{email} at {address}, {phone}, {ssn}"
    once = SCRUBBER.scrub(text)

    assert SCRUBBER.scrub(once) == once


@property_test
@given(text=st.text(max_size=200))
def test_scrub_never_crashes_on_arbitrary_input(text: str) -> None:
    """INVARIANT: scrub()/detect() are total functions over arbitrary text."""
    assert isinstance(SCRUBBER.scrub(text), str)
    assert isinstance(SCRUBBER.detect(text), list)


@pytest.mark.parametrize("text", ["", "   \n\t  "])
def test_degenerate_input(text: str) -> None:
    """Empty and whitespace-only input round-trip unchanged."""
    assert SCRUBBER.scrub(text) == text
    assert SCRUBBER.detect(text) == []
