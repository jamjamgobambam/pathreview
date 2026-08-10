"""Regression tests for the PII scrubber defects found via issue #111.

https://github.com/ascherj/pathreview/issues/111

This file started life as the *reproduction* for #111: every test below was
written to fail, and was marked ``xfail(strict=True)`` so the suite stayed green
while the fix was discussed on the issue thread. The fix has since landed in
``safety/pii_scrubber.py``, every marker flipped to ``XPASS``, and the markers
are gone -- these now assert the corrected behavior and guard against the
defects coming back.

The values are not hand-picked. Each ``@example`` is the minimal counterexample
``hypothesis`` shrank to when the properties in
``test_pii_scrubber_properties.py`` first ran against the unfixed scrubber, so
they are pinned here rather than left to the random seed.

The three defects, all in ``safety/pii_scrubber.py``:

1. **Phone separators omitted whitespace.** The separator classes were ``[-.]?``,
   so every space-separated number -- the dominant written form -- went
   unmatched, including ``(555) 123-4567``.
2. **``phone_intl`` consumed only the country code.** This was *worse than a
   miss*: ``+44 20 7946 0958`` became ``[REDACTED] 20 7946 0958``, output that
   looks scrubbed to a reviewer while leaking the subscriber number.
3. **``re.IGNORECASE`` let address abbreviations match inside words.** Lowercased,
   the two-letter suffixes ``St``/``Dr``/``Pl`` matched inside ``applications``
   and ``adr``, so ``5 years developing Python applications`` collapsed to
   ``[REDACTED]ications``.
"""

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from safety.pii_scrubber import PIIScrubber

pytestmark = pytest.mark.unit

ISSUE = "https://github.com/ascherj/pathreview/issues/111"

# `PIIScrubber` is stateless, and hypothesis rejects function-scoped fixtures
# under `@given` because they are not reset between generated examples.
SCRUBBER = PIIScrubber()

DIGITS = "0123456789"
SEPARATORS = st.sampled_from(["-", ".", " ", ""])

property_test = settings(max_examples=200, deadline=None)


@pytest.fixture
def scrubber() -> PIIScrubber:
    """Create a PIIScrubber instance."""
    return PIIScrubber()


# ---------------------------------------------------------------------------
# Strategies -- randomized but valid PII, the piece issue #111 says is missing.
# ---------------------------------------------------------------------------


@st.composite
def us_phones(draw: st.DrawFn) -> str:
    """Valid, human-written US phone numbers across separator/format variants."""
    area = draw(st.text(alphabet=DIGITS, min_size=3, max_size=3))
    exchange = draw(st.text(alphabet=DIGITS, min_size=3, max_size=3))
    line = draw(st.text(alphabet=DIGITS, min_size=4, max_size=4))
    sep1, sep2 = draw(SEPARATORS), draw(SEPARATORS)
    area_part = f"({area})" if draw(st.booleans()) else area
    return f"{area_part}{sep1}{exchange}{sep2}{line}"


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
    return f"+{country} " + " ".join(groups)


# ---------------------------------------------------------------------------
# Defect 1 -- phone separators omitted whitespace.
# ---------------------------------------------------------------------------


@property_test
@given(us_phones())
@example("000-000 0000")  # hypothesis-shrunk counterexample
@example("(555) 123-4567")  # the most common written US format
def test_us_phone_never_survives_scrub(phone: str) -> None:
    """INVARIANT: a generated US phone number never appears in scrub() output."""
    assert phone not in SCRUBBER.scrub(f"Call me at {phone} today")


@property_test
@given(intl_phones())
@example("+1 00 000")  # hypothesis-shrunk counterexample
@example("+44 20 7946 0958")
def test_intl_phone_never_leaks_a_digit_group(phone: str) -> None:
    """INVARIANT: no digit group of an international number survives scrub()."""
    output = SCRUBBER.scrub(f"Reach me at {phone}")
    leaked = [g for g in phone.lstrip("+").split() if len(g) >= 3 and g in output]
    assert not leaked, f"leaked {leaked} in {output!r}"


@pytest.mark.parametrize(
    "phone",
    [
        "(555) 123-4567",
        "555 123 4567",
        "+1 555 123 4567",
    ],
)
def test_space_separated_phone_is_redacted(scrubber: PIIScrubber, phone: str) -> None:
    """Concrete formats the example suite failed on before the fix."""
    assert "[REDACTED]" in scrubber.scrub(f"Contact: {phone}")


def test_intl_phone_is_redacted_whole(scrubber: PIIScrubber) -> None:
    """The partial-redaction leak is closed: the whole number goes, not just +44.

    Before the fix this returned ``"[REDACTED] 20 7946 0958"`` -- output that
    reads as scrubbed while the subscriber number sits beside it.
    """
    assert scrubber.scrub("+44 20 7946 0958") == "[REDACTED]"


# ---------------------------------------------------------------------------
# Defect 2 -- IGNORECASE made address abbreviations match inside words.
# ---------------------------------------------------------------------------


@property_test
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=40))
@example("adr")  # hypothesis-shrunk counterexample: contains "dr" (Drive)
@example("years developing python applications")  # contains "pl" (Place)
def test_prose_is_not_redacted_as_an_address(prose: str) -> None:
    """INVARIANT: a digit followed by ordinary prose is not PII."""
    text = f"I worked for 5 {prose}"
    assert "[REDACTED]" not in SCRUBBER.scrub(text), f"false positive on {text!r}"


# ---------------------------------------------------------------------------
# Control -- proves the properties fail on real defects, not on everything.
# This one passed before the fix too, and must keep passing after it.
# ---------------------------------------------------------------------------


@property_test
@given(
    local=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=10),
    domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
    tld=st.sampled_from(["com", "org", "co.uk", "io", "dev"]),
)
def test_email_never_survives_scrub(local: str, domain: str, tld: str) -> None:
    """The email regex held up under randomized input before and after the fix."""
    email = f"{local}@{domain}.{tld}"
    assert email not in SCRUBBER.scrub(f"Contact {email} please")
