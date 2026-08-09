"""Tests for pii_scrubber.py"""

import pytest

from safety.pii_scrubber import PIIScrubber


@pytest.mark.unit
class TestPIIScrubber:
    """Test suite for PIIScrubber."""

    @pytest.fixture
    def scrubber(self) -> PIIScrubber:
        """Create a PIIScrubber instance."""
        return PIIScrubber()

    def test_email_redaction(self, scrubber: PIIScrubber) -> None:
        """Test email address is redacted."""
        text = "Contact me at john.doe@example.com for more info."
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "john.doe@example.com" not in scrubbed

    def test_multiple_emails_redacted(self, scrubber: PIIScrubber) -> None:
        """Test multiple email addresses are redacted."""
        text = "Email alice@example.com or bob@company.org"
        scrubbed = scrubber.scrub(text)

        assert scrubbed.count("[REDACTED]") >= 2
        assert "alice@example.com" not in scrubbed
        assert "bob@company.org" not in scrubbed

    def test_us_phone_number_redaction(self, scrubber: PIIScrubber) -> None:
        """Test US phone number is redacted."""
        text = "Call me at (555) 123-4567"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "555" not in scrubbed or "1234567" not in scrubbed

    def test_us_phone_formats(self, scrubber: PIIScrubber) -> None:
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

    # --- Reproduction tests for issue #146 ---

    def test_paren_phone_reproduces_bug(self, scrubber: PIIScrubber) -> None:
        """Reproduction for issue #146: parenthesized phone number is not
        detected or scrubbed due to missing whitespace in the separator
        regex. EXPECTED TO FAIL until the fix is applied."""
        text = "Call me at (324) 901-1234"

        detected = scrubber.detect(text)
        scrubbed = scrubber.scrub(text)

        assert len(detected) > 0, "BUG: detect() found no PII for paren phone"
        assert "[REDACTED]" in scrubbed, "BUG: scrub() did not redact paren phone"

    def test_paren_phone_detect_reproduces_bug(self, scrubber: PIIScrubber) -> None:
        """Reproduction for issue #146: detect() fails to find parenthesized
        phone numbers. EXPECTED TO FAIL until the fix is applied."""
        text = "Call me at (324) 901-1234"
        detected = scrubber.detect(text)
        assert len(detected) > 0, "BUG: detect() found no PII for paren phone"

    def test_paren_phone_scrub_reproduces_bug(self, scrubber: PIIScrubber) -> None:
        """Reproduction for issue #146: scrub() fails to redact parenthesized
        phone numbers. EXPECTED TO FAIL until the fix is applied."""
        text = "Call me at (324) 901-1234"
        scrubbed = scrubber.scrub(text)
        assert "[REDACTED]" in scrubbed, "BUG: scrub() did not redact paren phone"

    # --- Edge-case tests for parenthesized phone format (issue #146) ---

    def test_phone_paren_no_space_after_close(self, scrubber: PIIScrubber) -> None:
        """Test parenthesized phone with no space after closing paren."""
        text = "Call me at (555)123-4567"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "(555)123-4567" not in scrubbed

    def test_phone_paren_dash_after_close(self, scrubber: PIIScrubber) -> None:
        """Test parenthesized phone with a dash after closing paren."""
        text = "Call me at (555)-123-4567"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "(555)-123-4567" not in scrubbed

    def test_phone_paren_dot_after_close(self, scrubber: PIIScrubber) -> None:
        """Test parenthesized phone with a dot after closing paren."""
        text = "Call me at (555).123.4567"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "(555).123.4567" not in scrubbed

    def test_detect_paren_phone_no_space(self, scrubber: PIIScrubber) -> None:
        """Test detect() finds parenthesized phone with no space."""
        text = "Phone: (555)123-4567"
        detected = scrubber.detect(text)

        phone_detections = [d for d in detected if "phone" in d["type"]]
        assert len(phone_detections) > 0
        assert "555" in phone_detections[0]["value"]

    def test_paren_phone_only_pii_detected(self, scrubber: PIIScrubber) -> None:
        """Test detect() is not empty when a parenthesized phone number
        is the only PII in the text (the core reported bug)."""
        text = "You can reach the office at (555) 123-4567 anytime."
        detected = scrubber.detect(text)

        assert len(detected) > 0
        assert any("phone" in d["type"] for d in detected)

    def test_paren_phone_no_false_positive_on_short_numbers(self, scrubber: PIIScrubber) -> None:
        """Test that unrelated parenthesized short numbers are not misdetected."""
        text = "See note (12) on page 4 for details."
        detected = scrubber.detect(text)

        phone_detections = [d for d in detected if "phone" in d["type"]]
        assert len(phone_detections) == 0

    def test_phone_country_code_with_parens(self, scrubber: PIIScrubber) -> None:
        """Test country code combined with parenthesized area code."""
        formats = [
            "+1 (555) 123-4567",
            "1 (555) 123-4567",
            "+1(555)123-4567",
        ]
        for phone in formats:
            text = f"Contact: {phone}"
            scrubbed = scrubber.scrub(text)
            assert "[REDACTED]" in scrubbed, f"Failed to redact: {phone}"

    def test_multiple_paren_phones_in_one_string(self, scrubber: PIIScrubber) -> None:
        """Test that multiple parenthesized phone numbers are all redacted."""
        text = "Call (555) 123-4567 or (555) 987-6543 for support."
        scrubbed = scrubber.scrub(text)
        assert scrubbed.count("[REDACTED]") >= 2
        assert "(555) 123-4567" not in scrubbed
        assert "(555) 987-6543" not in scrubbed

    def test_malformed_two_digit_area_code_not_matched(self, scrubber: PIIScrubber) -> None:
        """Test that a 2-digit area code is NOT matched as a phone number."""
        text = "Call (55) 123-4567 for info."
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) == 0

    def test_phone_with_trailing_punctuation(self, scrubber: PIIScrubber) -> None:
        """Test parenthesized phone followed immediately by punctuation."""
        cases = [
            "Call (555) 123-4567.",
            "Call (555) 123-4567,",
            "Call (555) 123-4567!",
        ]
        for text in cases:
            scrubbed = scrubber.scrub(text)
            assert "[REDACTED]" in scrubbed, f"Failed to redact in: {text}"

    def test_phone_inside_quotes(self, scrubber: PIIScrubber) -> None:
        """Test parenthesized phone number inside quotation marks."""
        text = "The number listed was '(555) 123-4567' in the document."
        scrubbed = scrubber.scrub(text)
        assert "[REDACTED]" in scrubbed
        assert "(555) 123-4567" not in scrubbed

    def test_phone_all_spaces_separator(self, scrubber: PIIScrubber) -> None:
        """Test phone number written with spaces as all separators."""
        text = "Contact: 555 123 4567"
        scrubbed = scrubber.scrub(text)
        assert "[REDACTED]" in scrubbed
        assert "555 123 4567" not in scrubbed

    def test_ssn_not_matched_as_phone(self, scrubber: PIIScrubber) -> None:
        """Test that an SSN (NNN-NN-NNNN) is not matched as a phone_us number."""
        text = "SSN: 123-45-6789"
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) == 0

    def test_seven_digit_number_not_matched(self, scrubber: PIIScrubber) -> None:
        """Test that a 7-digit number without area code is NOT matched."""
        text = "Old local number: 123-4567"
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) == 0

    def test_phone_detect_position_accuracy_paren_format(self, scrubber: PIIScrubber) -> None:
        """Test that start/end positions are accurate for parenthesized format."""
        text = "Call me at (555) 123-4567 today."
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) > 0
        item = phone_detections[0]
        extracted = text[item["start"] : item["end"]]
        assert "555" in extracted
        assert "123" in extracted
        assert "4567" in extracted

    def test_phone_country_code_with_dot_separator(self, scrubber: PIIScrubber) -> None:
        """Test country code with dot separator is redacted."""
        text = "Call +1.555.123.4567 for help."
        scrubbed = scrubber.scrub(text)
        assert "[REDACTED]" in scrubbed
        assert "+1.555.123.4567" not in scrubbed

    def test_phone_country_code_with_dash_separator(self, scrubber: PIIScrubber) -> None:
        """Test country code with dash separator is redacted."""
        text = "Call +1-555-123-4567 for help."
        scrubbed = scrubber.scrub(text)
        assert "[REDACTED]" in scrubbed
        assert "+1-555-123-4567" not in scrubbed

    def test_phone_four_digit_area_code_not_matched(self, scrubber: PIIScrubber) -> None:
        """Test that a 4-digit area code is NOT matched as a phone number."""
        text = "Number: (5555) 123-4567"
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) == 0

    def test_phone_with_letters_not_matched(self, scrubber: PIIScrubber) -> None:
        """Test that alphanumeric strings are not matched as phone numbers."""
        text = "Code: (555) 123-456A"
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) == 0

    def test_year_range_not_matched_as_phone(self, scrubber: PIIScrubber) -> None:
        """Test that a year range like 2023-2024 is not matched as a phone number."""
        text = "Report covers years 2023-2024."
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) == 0

    def test_phone_no_separators_ten_digits(self, scrubber: PIIScrubber) -> None:
        """Test that a raw 10-digit number is redacted (conservative scrubber bias)."""
        text = "Contact: 5551234567"
        scrubbed = scrubber.scrub(text)
        assert "[REDACTED]" in scrubbed

    def test_phone_does_not_merge_across_newlines(self, scrubber: PIIScrubber) -> None:
        """Test that separate numbers on different lines are NOT merged into
        a single false-positive phone number (e.g. table columns)."""
        text = "Row values:\n324\n901\n1234"
        detected = scrubber.detect(text)
        phone_detections = [d for d in detected if d["type"] == "phone_us"]
        assert len(phone_detections) == 0

    # --- End edge-case tests ---

    def test_international_phone_redaction(self, scrubber: PIIScrubber) -> None:
        """Test international phone number is redacted."""
        text = "Reach me at +44 20 7946 0958"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed or "20" not in scrubbed

    def test_ssn_redaction(self, scrubber: PIIScrubber) -> None:
        """Test SSN is redacted."""
        text = "SSN: 123-45-6789"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed
        assert "123-45-6789" not in scrubbed

    def test_ssn_variations(self, scrubber: PIIScrubber) -> None:
        """Test various SSN formats are handled."""
        ssns = [
            "123-45-6789",
            "987-65-4321",
        ]

        for ssn in ssns:
            text = f"SSN: {ssn}"
            scrubbed = scrubber.scrub(text)
            assert ssn not in scrubbed

    def test_street_address_redaction(self, scrubber: PIIScrubber) -> None:
        """Test street address is redacted."""
        text = "Address: 123 Main Street, Apt 4"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed or "123" not in scrubbed

    def test_text_with_no_pii(self, scrubber: PIIScrubber) -> None:
        """Test text with no PII is returned unchanged."""
        text = "This is a normal paragraph with no personal information."
        scrubbed = scrubber.scrub(text)

        assert scrubbed == text
        assert "[REDACTED]" not in scrubbed

    def test_detect_returns_list_of_pii(self, scrubber: PIIScrubber) -> None:
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

    def test_detect_email_pii(self, scrubber: PIIScrubber) -> None:
        """Test detect() finds email PII."""
        text = "Contact: alice@example.com"
        detected = scrubber.detect(text)

        assert len(detected) > 0
        email_detections = [d for d in detected if d["type"] == "email"]
        assert len(email_detections) > 0
        assert "alice@example.com" in email_detections[0]["value"]

    def test_detect_phone_pii(self, scrubber: PIIScrubber) -> None:
        """Test detect() finds phone number PII."""
        text = "Phone: (555) 123-4567"
        detected = scrubber.detect(text)

        phone_detections = [d for d in detected if "phone" in d["type"]]
        assert len(phone_detections) > 0

    def test_detect_ssn_pii(self, scrubber: PIIScrubber) -> None:
        """Test detect() finds SSN PII."""
        text = "SSN: 123-45-6789"
        detected = scrubber.detect(text)

        ssn_detections = [d for d in detected if d["type"] == "ssn"]
        assert len(ssn_detections) > 0

    def test_detect_positions_accurate(self, scrubber: PIIScrubber) -> None:
        """Test that detected positions are accurate."""
        text = "Email is john@example.com here."
        detected = scrubber.detect(text)

        for item in detected:
            if item["type"] == "email":
                start = item["start"]
                end = item["end"]
                extracted = text[start:end]
                assert "john@example.com" in extracted

    def test_detect_multiple_pii_items(self, scrubber: PIIScrubber) -> None:
        """Test detecting multiple PII items."""
        text = "John: 555-123-4567, jane@example.com, SSN: 987-65-4321"
        detected = scrubber.detect(text)

        assert len(detected) >= 2

    def test_case_insensitive_email_matching(self, scrubber: PIIScrubber) -> None:
        """Test email matching is case insensitive."""
        text = "Contact John.Doe@Example.COM"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed

    def test_complex_email_addresses(self, scrubber: PIIScrubber) -> None:
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

    def test_phone_at_start_of_text(self, scrubber: PIIScrubber) -> None:
        """Test phone number at start of text."""
        text = "(555) 123-4567 is my phone number."
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed

    def test_phone_at_end_of_text(self, scrubber: PIIScrubber) -> None:
        """Test phone number at end of text."""
        text = "My phone is 555-123-4567"
        scrubbed = scrubber.scrub(text)

        assert "[REDACTED]" in scrubbed

    def test_address_variations(self, scrubber: PIIScrubber) -> None:
        """Test various street address formats."""
        addresses = [
            "123 Main Street",
            "456 Oak Avenue",
            "789 Elm Road",
        ]

        for addr in addresses:
            text = f"Address: {addr}"
            scrubbed = scrubber.scrub(text)
            assert "[REDACTED]" in scrubbed or addr not in scrubbed

    def test_empty_text(self, scrubber: PIIScrubber) -> None:
        """Test with empty text."""
        text = ""
        scrubbed = scrubber.scrub(text)
        assert scrubbed == ""

        detected = scrubber.detect(text)
        assert detected == []

    def test_whitespace_only(self, scrubber: PIIScrubber) -> None:
        """Test with whitespace only."""
        text = "   \n\t  "
        scrubbed = scrubber.scrub(text)
        assert scrubbed == text

    def test_mixed_pii_and_text(self, scrubber: PIIScrubber) -> None:
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

        assert "TechCorp" in scrubbed
        assert "Python" in scrubbed
        assert "AWS" in scrubbed
        assert "[REDACTED]" in scrubbed
        assert "john.smith@company.com" not in scrubbed
        assert "555-123-4567" not in scrubbed

    def test_scrub_idempotent(self, scrubber: PIIScrubber) -> None:
        """Test that scrubbing twice produces same result."""
        text = "Email: test@example.com"
        scrubbed_once = scrubber.scrub(text)
        scrubbed_twice = scrubber.scrub(scrubbed_once)

        assert scrubbed_once == scrubbed_twice

    def test_detect_no_false_positives(self, scrubber: PIIScrubber) -> None:
        """Test that detect doesn't flag legitimate text as PII."""
        text = "The project uses version 1.2.3. See https://example.com"
        detected = scrubber.detect(text)

        flagged = [d for d in detected if d["type"] in ("ssn", "phone_us", "phone_intl")]
        assert len(flagged) == 0
