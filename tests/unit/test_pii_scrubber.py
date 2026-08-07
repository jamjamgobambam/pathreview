"""Tests for pii_scrubber.py"""

# Existing pytest fixtures and test methods in this module intentionally use
# pytest's untyped function style; keep strict mypy focused on production code.
# mypy: disable-error-code="no-untyped-def"

from string import ascii_letters, digits

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from safety.pii_scrubber import PIIScrubber


@st.composite
def email_values(draw):
    """Generate email values covered by the scrubber's email pattern."""
    first = draw(st.sampled_from(ascii_letters + digits))
    rest = draw(st.text(alphabet=ascii_letters + digits + "._%+-", min_size=0, max_size=12))
    domain = draw(st.text(alphabet=ascii_letters + digits, min_size=1, max_size=10))
    tld = draw(st.text(alphabet=ascii_letters, min_size=2, max_size=6))
    return f"{first}{rest}@{domain}.{tld}"


@st.composite
def us_phone_values(draw):
    """Generate supported US phone number formats."""
    area = draw(st.integers(min_value=200, max_value=999))
    exchange = draw(st.integers(min_value=200, max_value=999))
    subscriber = draw(st.integers(min_value=0, max_value=9999))
    style = draw(st.sampled_from(("hyphen", "parenthesized", "dot", "country", "compact")))
    area_text = f"{area:03d}"
    exchange_text = f"{exchange:03d}"
    subscriber_text = f"{subscriber:04d}"

    if style == "parenthesized":
        return f"({area_text}) {exchange_text}-{subscriber_text}"
    if style == "dot":
        return f"{area_text}.{exchange_text}.{subscriber_text}"
    if style == "country":
        return f"+1 {area_text} {exchange_text} {subscriber_text}"
    if style == "compact":
        return f"{area_text}{exchange_text}{subscriber_text}"
    return f"{area_text}-{exchange_text}-{subscriber_text}"


@st.composite
def international_phone_values(draw):
    """Generate international phone values with supported separators."""
    country = draw(st.integers(min_value=1, max_value=999))
    groups = [draw(st.text(alphabet=digits, min_size=2, max_size=4)) for _ in range(3)]
    separator = draw(st.sampled_from((" ", "-", ".")))
    return f"+{country}{separator}{separator.join(groups)}"


@st.composite
def ssn_values(draw):
    """Generate valid SSN-shaped values accepted by the scrubber."""
    area = draw(st.integers(min_value=1, max_value=665))
    group = draw(st.integers(min_value=1, max_value=99))
    serial = draw(st.integers(min_value=1, max_value=9999))
    return f"{area:03d}-{group:02d}-{serial:04d}"


@st.composite
def street_address_values(draw):
    """Generate simple street addresses covered by the address pattern."""
    number = draw(st.integers(min_value=1, max_value=9999))
    street = draw(st.sampled_from(("Main", "Oak", "Elm", "Maple", "Pine")))
    suffix = draw(st.sampled_from(("Street", "Avenue", "Road", "Drive", "Lane")))
    return f"{number} {street} {suffix}"


pii_values = st.one_of(
    email_values(),
    us_phone_values(),
    international_phone_values(),
    ssn_values(),
    street_address_values(),
)


@pytest.mark.unit
class TestPIIScrubber:
    """Test suite for PIIScrubber."""

    @pytest.fixture
    def scrubber(self):
        """Create a PIIScrubber instance."""
        return PIIScrubber()

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
            assert addr not in scrubbed
            assert "[REDACTED]" in scrubbed

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
        assert detected == []

    @given(pii=pii_values)
    @settings(max_examples=50, deadline=None)
    def test_scrub_redacts_generated_pii(self, pii):
        """Test that generated supported PII is absent after scrubbing."""
        text = f"Profile record: {pii}"

        scrubbed = PIIScrubber().scrub(text)

        assert pii not in scrubbed
        assert "[REDACTED]" in scrubbed

    @given(pii=pii_values)
    @settings(max_examples=50, deadline=None)
    def test_detect_reports_generated_pii_span(self, pii):
        """Test that generated PII is detected with an accurate source span."""
        text = f"Profile record: {pii}"

        detections = PIIScrubber().detect(text)
        matching_detections = [detection for detection in detections if detection["value"] == pii]

        assert matching_detections
        for detection in matching_detections:
            assert text[detection["start"] : detection["end"]] == detection["value"]

    @given(pii=pii_values)
    @settings(max_examples=50, deadline=None)
    def test_scrub_generated_pii_is_idempotent(self, pii):
        """Test that generated PII remains stable after a second scrub."""
        text = f"Profile record: {pii}"
        scrubber = PIIScrubber()
        scrubbed_once = scrubber.scrub(text)

        assert scrubber.scrub(scrubbed_once) == scrubbed_once
