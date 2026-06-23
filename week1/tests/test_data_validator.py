"""
Pytest test suite for week1/data_validator.py

Covers:
  - Valid inputs (email + phone combinations)
  - Invalid email scenarios
  - Invalid phone scenarios
  - Both fields invalid
  - Edge cases (empty strings, whitespace, unicode)
  - Output schema contract compliance
  - handle() return-type guarantees

Run:
    pytest week1/tests/test_data_validator.py -v
    pytest week1/tests/test_data_validator.py -v --tb=short
"""

import sys
from pathlib import Path

import pytest

# ── Resolve import path ──────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_validator import handle, INPUT_SCHEMA, OUTPUT_SCHEMA  # noqa: E402


# ═════════════════════════════════════════════════════════════════════
# FIXTURES
# ═════════════════════════════════════════════════════════════════════

@pytest.fixture
def valid_payload():
    """A payload where both fields are valid."""
    return {"email": "bijay.algo@example.com", "phone": "+977-9801234567"}


@pytest.fixture
def invalid_email_payload():
    """A payload with a malformed email and a valid phone."""
    return {"email": "not-an-email.com", "phone": "9841000111"}


@pytest.fixture
def invalid_phone_payload():
    """A payload with a valid email and a phone that is too short."""
    return {"email": "user@example.com", "phone": "123"}


# ═════════════════════════════════════════════════════════════════════
# 1. RETURN-TYPE CONTRACT
# ═════════════════════════════════════════════════════════════════════

class TestReturnTypeContract:
    """handle() must always return a dict with the four required keys."""

    def test_returns_dict(self, valid_payload):
        assert isinstance(handle(valid_payload), dict)

    def test_contains_is_valid_key(self, valid_payload):
        assert "is_valid" in handle(valid_payload)

    def test_contains_email_valid_key(self, valid_payload):
        assert "email_valid" in handle(valid_payload)

    def test_contains_phone_valid_key(self, valid_payload):
        assert "phone_valid" in handle(valid_payload)

    def test_contains_errors_key(self, valid_payload):
        assert "errors" in handle(valid_payload)

    def test_errors_is_list(self, valid_payload):
        assert isinstance(handle(valid_payload)["errors"], list)

    def test_is_valid_is_bool(self, valid_payload):
        assert isinstance(handle(valid_payload)["is_valid"], bool)

    def test_no_extra_keys(self, valid_payload):
        expected_keys = {"is_valid", "email_valid", "phone_valid", "errors"}
        assert set(handle(valid_payload).keys()) == expected_keys


# ═════════════════════════════════════════════════════════════════════
# 2. VALID INPUTS
# ═════════════════════════════════════════════════════════════════════

class TestValidInputs:

    @pytest.mark.parametrize("email,phone", [
        ("bijay.algo@example.com",   "+977-9801234567"),
        ("user+tag@domain.io",       "+1 (415) 555-0172"),
        ("admin@mail.university.edu","9841000111"),
        ("hello@my-company.co.uk",   "+44 20 7946 0958"),
        ("123user@example.org",      "(01) 234-5678"),
        ("a@b.co",                   "+1-800-555-0199"),
    ])
    def test_valid_pair(self, email, phone):
        result = handle({"email": email, "phone": phone})
        assert result["is_valid"]     is True,  f"Expected is_valid=True for {email}, {phone}"
        assert result["email_valid"]  is True,  f"Expected email_valid=True for {email}"
        assert result["phone_valid"]  is True,  f"Expected phone_valid=True for {phone}"
        assert result["errors"]       == [],    f"Expected no errors for {email}, {phone}"


# ═════════════════════════════════════════════════════════════════════
# 3. INVALID EMAIL SCENARIOS
# ═════════════════════════════════════════════════════════════════════

class TestInvalidEmail:

    @pytest.mark.parametrize("bad_email", [
        "not-an-email.com",      # missing @
        "@@broken",              # double @
        "user@",                 # no domain
        "@domain.com",           # no local part
        "user@domain",           # no TLD
        "",                      # empty string
        "   ",                   # whitespace only
        "user @domain.com",      # space in local part
    ])
    def test_bad_email_fails(self, bad_email):
        result = handle({"email": bad_email, "phone": "+977-9801234567"})
        assert result["email_valid"] is False, f"Expected email_valid=False for '{bad_email}'"
        assert result["is_valid"]    is False
        assert len(result["errors"]) >= 1
        assert any("email" in err.lower() for err in result["errors"])

    def test_bad_email_does_not_affect_phone_result(self, invalid_email_payload):
        result = handle(invalid_email_payload)
        assert result["phone_valid"] is True


# ═════════════════════════════════════════════════════════════════════
# 4. INVALID PHONE SCENARIOS
# ═════════════════════════════════════════════════════════════════════

class TestInvalidPhone:

    @pytest.mark.parametrize("bad_phone", [
        "123",                   # too short (< 7 digits)
        "",                      # empty string
        "abc-xyz",               # letters only
        "+9779999999999999",     # exceeds 15-digit ITU-T E.164 max
        "!!@@##",                # special chars, no digits
    ])
    def test_bad_phone_fails(self, bad_phone):
        result = handle({"email": "user@example.com", "phone": bad_phone})
        assert result["phone_valid"] is False, f"Expected phone_valid=False for '{bad_phone}'"
        assert result["is_valid"]    is False
        assert any("phone" in err.lower() for err in result["errors"])

    def test_bad_phone_does_not_affect_email_result(self, invalid_phone_payload):
        result = handle(invalid_phone_payload)
        assert result["email_valid"] is True


# ═════════════════════════════════════════════════════════════════════
# 5. BOTH FIELDS INVALID
# ═════════════════════════════════════════════════════════════════════

class TestBothInvalid:

    def test_two_errors_returned(self):
        result = handle({"email": "@@broken", "phone": "abc"})
        assert result["is_valid"]    is False
        assert result["email_valid"] is False
        assert result["phone_valid"] is False
        assert len(result["errors"]) == 2

    def test_empty_strings_both_invalid(self):
        result = handle({"email": "", "phone": ""})
        assert result["is_valid"] is False
        assert len(result["errors"]) == 2


# ═════════════════════════════════════════════════════════════════════
# 6. EDGE CASES
# ═════════════════════════════════════════════════════════════════════

class TestEdgeCases:

    def test_missing_email_key_defaults_gracefully(self):
        """handle() should not raise even if 'email' key is absent."""
        result = handle({"phone": "+977-9801234567"})
        assert result["email_valid"] is False

    def test_missing_phone_key_defaults_gracefully(self):
        """handle() should not raise even if 'phone' key is absent."""
        result = handle({"email": "user@example.com"})
        assert result["phone_valid"] is False

    def test_extra_keys_ignored(self):
        """Extra keys in input_data should not cause errors."""
        result = handle({
            "email": "user@example.com",
            "phone": "+977-9801234567",
            "name":  "Bijay"
        })
        assert result["is_valid"] is True

    def test_minimum_valid_email(self):
        result = handle({"email": "a@b.co", "phone": "1234567"})
        assert result["email_valid"] is True

    def test_exactly_7_digit_phone(self):
        result = handle({"email": "user@example.com", "phone": "1234567"})
        assert result["phone_valid"] is True

    def test_exactly_15_digit_phone(self):
        result = handle({"email": "user@example.com", "phone": "+123456789012345"})
        assert result["phone_valid"] is True


# ═════════════════════════════════════════════════════════════════════
# 7. SCHEMA PRESENCE
# ═════════════════════════════════════════════════════════════════════

class TestSchemaPresence:

    def test_input_schema_is_dict(self):
        assert isinstance(INPUT_SCHEMA, dict)

    def test_output_schema_is_dict(self):
        assert isinstance(OUTPUT_SCHEMA, dict)

    def test_input_schema_has_required_field(self):
        assert "required" in INPUT_SCHEMA
        assert "email" in INPUT_SCHEMA["required"]
        assert "phone" in INPUT_SCHEMA["required"]

    def test_output_schema_has_is_valid_property(self):
        assert "is_valid" in OUTPUT_SCHEMA["properties"]
