"""Reproduction for issue #111 — no property-based tests for the PII scrubber.

https://github.com/ascherj/pathreview/issues/111

This file is *evidence*, not the final deliverable. It pins the concrete PII
formats that `PIIScrubber` fails to redact, so the defects are visible and
regression-tested while the fix is discussed on the issue thread.

Every test here is marked ``xfail(strict=True)``: the suite stays green today,
and the moment someone fixes ``safety/pii_scrubber.py`` these flip to
unexpected-pass and fail loudly, prompting removal of the marker.

Two root causes, both in ``safety/pii_scrubber.py``:

1. The phone separator classes are ``[-.]?`` and do not include whitespace, so
   space-separated numbers never match. ``phone_intl`` is worse than a miss --
   it consumes only the country code, leaving the subscriber number in output
   that *looks* redacted.
2. ``scrub()`` applies ``re.IGNORECASE`` to ``street_address``, whose
   alternation contains two-letter abbreviations (``St``, ``Dr``, ``Pl``,
   ``Ct``). Lowercased, they match inside ordinary words.

The ``@example`` decorators below are the counterexamples hypothesis shrank to
on first run. They are pinned so these tests fail deterministically rather than
depending on the random seed.
"""

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from safety.pii_scrubber import PIIScrubber

pytestmark = pytest.mark.unit

ISSUE = "https://github.com/ascherj/pathreview/issues/111"


@pytest.fixture
def scrubber() -> PIIScrubber:
    return PIIScrubber()


# ---------------------------------------------------------------------------
# Strategies -- randomized but valid PII, the piece issue #111 says is missing.
# ---------------------------------------------------------------------------

DIGITS = "0123456789"
SEPARATORS = st.sampled_from(["-", ".", " ", ""])


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
# Defect 1 -- phone separators omit whitespace.
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason=f"phone_us separators omit space -- {ISSUE}")
@settings(max_examples=200, deadline=None)
@given(us_phones())
@example("000-000 0000")  # hypothesis-shrunk counterexample
@example("(555) 123-4567")  # the most common written US format
def test_property_us_phone_never_survives_scrub(phone: str) -> None:
    """INVARIANT: a generated US phone number never appears in scrub() output."""
    assert phone not in PIIScrubber().scrub(f"Call me at {phone} today")


@pytest.mark.xfail(strict=True, reason=f"phone_intl consumes only country code -- {ISSUE}")
@settings(max_examples=200, deadline=None)
@given(intl_phones())
@example("+1 00 000")  # hypothesis-shrunk counterexample
@example("+44 20 7946 0958")
def test_property_intl_phone_never_leaks_a_digit_group(phone: str) -> None:
    """INVARIANT: no digit group of an international number survives scrub()."""
    output = PIIScrubber().scrub(f"Reach me at {phone}")
    leaked = [g for g in phone.lstrip("+").split() if len(g) >= 3 and g in output]
    assert not leaked, f"leaked {leaked} in {output!r}"


@pytest.mark.xfail(strict=True, reason=f"space-separated phones unmatched -- {ISSUE}")
@pytest.mark.parametrize(
    "phone",
    [
        "(555) 123-4567",
        "555 123 4567",
        "+1 555 123 4567",
    ],
)
def test_regression_space_separated_phone_is_redacted(scrubber: PIIScrubber, phone: str) -> None:
    """Concrete formats the existing example suite already fails on."""
    assert "[REDACTED]" in scrubber.scrub(f"Contact: {phone}")


def test_regression_intl_phone_partial_redaction_leaks_subscriber(
    scrubber: PIIScrubber,
) -> None:
    """Documents current behavior: worse than a miss -- it *looks* redacted.

    Not xfail: this asserts what the scrubber does TODAY, so the leak is
    unmissable in the diff. Delete this test when the fix lands.
    """
    assert scrubber.scrub("+44 20 7946 0958") == "[REDACTED] 20 7946 0958"


# ---------------------------------------------------------------------------
# Defect 2 -- IGNORECASE makes address abbreviations match inside words.
# ---------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason=f"street_address false positives -- {ISSUE}")
@settings(max_examples=200, deadline=None)
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=40))
@example("adr")  # hypothesis-shrunk counterexample: contains "dr" (Drive)
@example("years developing python applications")  # contains "pl" (Place)
def test_property_prose_is_not_redacted_as_an_address(prose: str) -> None:
    """INVARIANT: a digit followed by ordinary prose is not PII."""
    text = f"I worked for 5 {prose}"
    assert "[REDACTED]" not in PIIScrubber().scrub(text), f"false positive on {text!r}"


# ---------------------------------------------------------------------------
# Control -- proves the properties fail on real defects, not on everything.
# ---------------------------------------------------------------------------


@settings(max_examples=200, deadline=None)
@given(
    local=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=10),
    domain=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
    tld=st.sampled_from(["com", "org", "co.uk", "io", "dev"]),
)
def test_property_email_never_survives_scrub(local: str, domain: str, tld: str) -> None:
    """PASSES. The email regex holds up under randomized input."""
    email = f"{local}@{domain}.{tld}"
    assert email not in PIIScrubber().scrub(f"Contact {email} please")
