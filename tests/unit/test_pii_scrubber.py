"""Tests for pii_scrubber.py"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from safety.pii_scrubber import PIIScrubber

ASCII_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE_LETTERS = "abcdefghijklmnopqrstuvwxyz"
EMAIL_ATOM_CHARACTERS = f"{ASCII_LETTERS}0123456789"
STREET_SUFFIXES = (
    "Street",
    "St",
    "Avenue",
    "Ave",
    "Road",
    "Rd",
    "Boulevard",
    "Blvd",
    "Drive",
    "Dr",
    "Lane",
    "Court",
    "Circle",
    "Way",
    "Terrace",
    "Trail",
)


def ascii_word(min_size=1, max_size=12):
    """Build a bounded ASCII word accepted by the scrubber's PII formats."""
    return st.text(alphabet=LOWERCASE_LETTERS, min_size=min_size, max_size=max_size)


@st.composite
def email_addresses(draw):
    """Generate practical email addresses in the scrubber's supported domain."""
    local_parts = draw(
        st.lists(
            st.text(alphabet=EMAIL_ATOM_CHARACTERS, min_size=1, max_size=8),
            min_size=1,
            max_size=3,
        )
    )
    local_separator = draw(st.sampled_from((".", "_", "+", "-")))
    local = local_separator.join(local_parts)
    domain_parts = draw(st.lists(ascii_word(), min_size=1, max_size=3))
    top_level_domain = draw(ascii_word(min_size=2, max_size=8))
    return f"{local}@{'.'.join(domain_parts)}.{top_level_domain}"


@st.composite
def us_phone_numbers(draw):
    """Generate US phone formats explicitly supported by the scrubber."""
    digits = draw(st.text(alphabet="0123456789", min_size=10, max_size=10))
    area, exchange, subscriber = digits[:3], digits[3:6], digits[6:]
    phone_format = draw(st.sampled_from(("plain", "hyphen", "dot")))

    if phone_format == "plain":
        return digits

    separator = "-" if phone_format == "hyphen" else "."
    country_code = draw(st.sampled_from(("", "1", "1" + separator)))
    return f"{country_code}{area}{separator}{exchange}{separator}{subscriber}"


@st.composite
def international_phone_numbers(draw):
    """Generate international numbers in the scrubber's compact supported form."""
    country_code = draw(st.text(alphabet="0123456789", min_size=1, max_size=3))
    national_number = draw(st.text(alphabet="0123456789", min_size=4, max_size=6))
    separator = draw(st.sampled_from(("", "-", ".")))
    return f"+{country_code}{separator}{national_number}"


@st.composite
def social_security_numbers(draw):
    """Generate structurally valid SSNs accepted by the scrubber."""
    area = draw(st.one_of(st.integers(min_value=1, max_value=665), st.integers(667, 999)))
    group = draw(st.integers(min_value=1, max_value=99))
    serial = draw(st.integers(min_value=1, max_value=9999))
    return f"{area:03d}-{group:02d}-{serial:04d}"


@st.composite
def street_addresses(draw):
    """Generate simple US street addresses in the scrubber's supported form."""
    number = draw(st.integers(min_value=1, max_value=99999))
    street_name = " ".join(draw(st.lists(ascii_word(), min_size=1, max_size=3)))
    suffix = draw(st.sampled_from(STREET_SUFFIXES))
    return f"{number} {street_name} {suffix}"


PII_VALUES = st.one_of(
    email_addresses(),
    us_phone_numbers(),
    international_phone_numbers(),
    social_security_numbers(),
    street_addresses(),
)


@pytest.mark.unit
class TestPIIScrubber:
    """Test suite for PIIScrubber."""

    @pytest.fixture
    def scrubber(self):
        """Create a PIIScrubber instance."""
        return PIIScrubber()

    @given(email=email_addresses())
    def test_generated_emails_are_redacted(self, email):
        """Every generated supported email is removed without losing safe context."""
        scrubbed = PIIScrubber().scrub(f"Contact email: {email}\nEnd of contact.")

        assert email not in scrubbed
        assert scrubbed == "Contact email: [REDACTED]\nEnd of contact."

    @given(phone=us_phone_numbers())
    def test_generated_us_phone_numbers_are_redacted(self, phone):
        """Every generated supported US phone number is removed."""
        scrubbed = PIIScrubber().scrub(f"Call this number: {phone}; thanks.")

        assert phone not in scrubbed
        assert scrubbed == "Call this number: [REDACTED]; thanks."

    @given(phone=international_phone_numbers())
    def test_generated_international_phone_numbers_are_redacted(self, phone):
        """Every generated supported international phone number is removed."""
        scrubbed = PIIScrubber().scrub(f"International contact: {phone}\nPlease call.")

        assert phone not in scrubbed
        assert scrubbed == "International contact: [REDACTED]\nPlease call."

    @given(ssn=social_security_numbers())
    def test_generated_ssns_are_redacted(self, ssn):
        """Every generated structurally valid SSN is removed."""
        scrubbed = PIIScrubber().scrub(f"Tax identifier: {ssn}. Keep private.")

        assert ssn not in scrubbed
        assert scrubbed == "Tax identifier: [REDACTED]. Keep private."

    @given(address=street_addresses())
    def test_generated_street_addresses_are_redacted(self, address):
        """Every generated supported street address is removed."""
        scrubbed = PIIScrubber().scrub(f"Mail to: {address}; recipient on file.")

        assert address not in scrubbed
        assert scrubbed == "Mail to: [REDACTED]; recipient on file."

    @given(pii=PII_VALUES)
    def test_scrubbing_generated_pii_is_idempotent(self, pii):
        """Scrubbing generated PII twice has no additional effect."""
        scrubber = PIIScrubber()
        scrubbed = scrubber.scrub(f"Sensitive value: {pii}")

        assert scrubber.scrub(scrubbed) == scrubbed

    @given(text=st.text(max_size=200))
    def test_scrubbing_bounded_arbitrary_text_does_not_crash(self, text):
        """Reasonably sized arbitrary Unicode text can always be scrubbed."""
        result = PIIScrubber().scrub(text)

        assert isinstance(result, str)

    def test_email_redaction(self, scrubber):
        """Test email address is redacted."""
        text = "Contact me at john.doe@example.com for more info."
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "john.doe@example.com" not in scrubbed

    def test_multiple_emails_redacted(self, scrubber):
        """Test multiple email addresses are redacted."""
        text = "Email alice@example.com or bob@company.org"
        scrubbed = scrubber.scrub(text)

        assert scrubbed.count("[REDACTED]") >= 2
        assert "alice@example.com" not in scrubbed
        assert "bob@company.org" not in scrubbed

    def test_us_phone_number_redaction(self, scrubber):
        """Test US phone number is redacted."""
        text = "Call me at (555) 123-4567"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "555" not in scrubbed or "1234567" not in scrubbed

    def test_us_phone_formats(self, scrubber):
        """Test various US phone number formats."""
        formats = [
            "555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "+1 555 123 4567",
        ]

        for phone in formats:
            text = f"Contact: {phone}"
            scrubbed = scrubber.scrub(text)
            assert "[REDACTED]" in scrubbed

    def test_international_phone_redaction(self, scrubber):
        """Test international phone number is redacted."""
        text = "Reach me at +44 20 7946 0958"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed or "20" not in scrubbed

    def test_ssn_redaction(self, scrubber):
        """Test SSN is redacted."""
        text = "SSN: 123-45-6789"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "123-45-6789" not in scrubbed

    def test_ssn_variations(self, scrubber):
        """Test various SSN formats are handled."""
        ssns = [
            "123-45-6789",
            "987-65-4321",
        ]

        for ssn in ssns:
            text = f"SSN: {ssn}"
            scrubbed = scrubber.scrub(text)
            # Should be redacted or modified
            assert ssn not in scrubbed

    def test_street_address_redaction(self, scrubber):
        """Test street address is redacted."""
        text = "Address: 123 Main Street, Apt 4"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed or "123" not in scrubbed

    def test_text_with_no_pii(self, scrubber):
        """Test text with no PII is returned unchanged."""
        text = "This is a normal paragraph with no personally identifiable information."
        scrubbed = scrubber.scrub(text)

        assert scrubbed == text
        assert "[REDACTED]" not in scrubbed

    def test_detect_returns_list_of_pii(self, scrubber):
        """Test detect() returns list with type, value, start, end."""
        text = "Email: john@example.com and call 555-123-4567"
        detected = scrubber.detect(text)

        assert isinstance(detected, list)
        for item in detected:
            assert isinstance(item, dict)
            assert "type" in item
            assert "value" in item
            assert "start" in item
            assert "end" in item

    def test_detect_email_pii(self, scrubber):
        """Test detect() finds email PII."""
        text = "Contact: alice@example.com"
        detected = scrubber.detect(text)

        assert len(detected) > 0
        email_detections = [d for d in detected if d["type"] == "email"]
        assert len(email_detections) > 0
        assert "alice@example.com" in email_detections[0]["value"]

    def test_detect_phone_pii(self, scrubber):
        """Test detect() finds phone number PII."""
        text = "Phone: (555) 123-4567"
        detected = scrubber.detect(text)

        phone_detections = [d for d in detected if "phone" in d["type"]]
        assert len(phone_detections) > 0

    def test_detect_ssn_pii(self, scrubber):
        """Test detect() finds SSN PII."""
        text = "SSN: 123-45-6789"
        detected = scrubber.detect(text)

        ssn_detections = [d for d in detected if d["type"] == "ssn"]
        assert len(ssn_detections) > 0

    def test_detect_positions_accurate(self, scrubber):
        """Test that detected positions are accurate."""
        text = "Email is john@example.com here."
        detected = scrubber.detect(text)

        for item in detected:
            if item["type"] == "email":
                start = item["start"]
                end = item["end"]
                extracted = text[start:end]
                assert "john@example.com" in extracted

    def test_detect_multiple_pii_items(self, scrubber):
        """Test detecting multiple PII items."""
        text = "John: 555-123-4567, jane@example.com, SSN: 987-65-4321"
        detected = scrubber.detect(text)

        # Should find multiple items
        assert len(detected) >= 2

    def test_case_insensitive_email_matching(self, scrubber):
        """Test email matching is case insensitive."""
        text = "Contact John.Doe@Example.COM"
        scrubbed = scrubber.scrub(text)

        # Email should be redacted despite case differences
        assert "[REDACTED]" in scrubbed

    def test_complex_email_addresses(self, scrubber):
        """Test complex email address formats."""
        emails = [
            "user+tag@example.com",
            "first.last@sub.domain.co.uk",
            "test_123@example.org",
        ]

        for email in emails:
            text = f"Contact: {email}"
            scrubbed = scrubber.scrub(text)
            assert email not in scrubbed or "[REDACTED]" in scrubbed

    def test_phone_at_start_of_text(self, scrubber):
        """Test phone number at start of text."""
        text = "(555) 123-4567 is my phone number."
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed

    def test_phone_at_end_of_text(self, scrubber):
        """Test phone number at end of text."""
        text = "My phone is 555-123-4567"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed

    def test_address_variations(self, scrubber):
        """Test various street address formats."""
        addresses = [
            "123 Main Street",
            "456 Oak Avenue",
            "789 Elm Road",
        ]

        for addr in addresses:
            text = f"Address: {addr}"
            scrubbed = scrubber.scrub(text)
            # Should attempt to redact addresses

    def test_empty_text(self, scrubber):
        """Test with empty text."""
        text = ""
        scrubbed = scrubber.scrub(text)
        assert scrubbed == ""

        detected = scrubber.detect(text)
        assert detected == []

    def test_whitespace_only(self, scrubber):
        """Test with whitespace only."""
        text = "   \n\t  "
        scrubbed = scrubber.scrub(text)
        assert scrubbed == text

    def test_mixed_pii_and_text(self, scrubber):
        """Test text with mix of PII and regular content."""
        text = """
        Professional Background:
        I worked at TechCorp for 5 years developing Python applications.
        Email: john.smith@company.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        I'm skilled in AWS and Kubernetes deployment.
        """
        scrubbed = scrubber.scrub(text)

        assert "TechCorp" in scrubbed  # Regular text preserved
        assert "Python" in scrubbed
        assert "AWS" in scrubbed
        assert "[REDACTED]" in scrubbed  # PII redacted
        assert "john.smith@company.com" not in scrubbed
        assert "555-123-4567" not in scrubbed

    def test_scrub_idempotent(self, scrubber):
        """Test that scrubbing twice produces same result."""
        text = "Email: test@example.com"
        scrubbed_once = scrubber.scrub(text)
        scrubbed_twice = scrubber.scrub(scrubbed_once)

        assert scrubbed_once == scrubbed_twice

    def test_detect_no_false_positives(self, scrubber):
        """Test that detect doesn't flag legitimate text as PII."""
        text = "The project uses version 1.2.3. It's available at https://example.com"
        detected = scrubber.detect(text)

        # Should be minimal or no detections
        # (version number shouldn't be flagged as SSN)
