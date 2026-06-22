"""
PyGene Week 1 Deliverable: Data Validator Function

Validates an email address and a phone number.
Defines JSON input/output schemas, includes 3 test cases,
and documents every logical step with inline comments.
"""

import re    # re: standard library for regular expressions
import json  # json: standard library for JSON serialisation


# ──────────────────────────────────────────────
# JSON INPUT SCHEMA
# Describes the expected shape of the function's input.
# ──────────────────────────────────────────────
INPUT_SCHEMA: dict = {
    "type": "object",           # The top-level value must be a JSON object
    "properties": {
        "email": {
            "type": "string",   # email must be a string
            "description": "An email address to validate (e.g. user@example.com)"
        },
        "phone": {
            "type": "string",   # phone must be a string (digits + optional formatting chars)
            "description": "A phone number to validate (e.g. +977-9801234567 or 9801234567)"
        }
    },
    "required": ["email", "phone"],  # Both fields are mandatory
    "additionalProperties": False    # No extra keys are allowed in the input
}


# ──────────────────────────────────────────────
# JSON OUTPUT SCHEMA
# Describes the shape of the value this function returns.
# ──────────────────────────────────────────────
OUTPUT_SCHEMA: dict = {
    "type": "object",             # The return value is a JSON object
    "properties": {
        "is_valid": {
            "type": "boolean",    # True if BOTH email AND phone pass; False otherwise
            "description": "Overall validation result"
        },
        "email_valid": {
            "type": "boolean",    # Whether the email passed its individual check
            "description": "True if the email address is well-formed"
        },
        "phone_valid": {
            "type": "boolean",    # Whether the phone passed its individual check
            "description": "True if the phone number is well-formed"
        },
        "errors": {
            "type": "array",      # A list (possibly empty) of human-readable error messages
            "items": {"type": "string"},
            "description": "List of validation error messages; empty when is_valid is True"
        }
    },
    "required": ["is_valid", "email_valid", "phone_valid", "errors"]
}


# ──────────────────────────────────────────────
# CORE VALIDATOR FUNCTION  (handle() contract)
# ──────────────────────────────────────────────
def handle(input_data: dict) -> dict:
    """
    PyGene entry-point function.

    Accepts a dict that conforms to INPUT_SCHEMA and returns a dict
    that conforms to OUTPUT_SCHEMA.

    Parameters
    ----------
    input_data : dict
        Must contain:
          - "email" (str): the email address to validate
          - "phone" (str): the phone number to validate

    Returns
    -------
    dict
        {
          "is_valid"    : bool,   # True only when both checks pass
          "email_valid" : bool,
          "phone_valid" : bool,
          "errors"      : list[str]
        }
    """

    # ── 1. Extract inputs ────────────────────────────────────────────
    email: str = input_data.get("email", "")   # Pull email; default to empty string if missing
    phone: str = input_data.get("phone", "")   # Pull phone; default to empty string if missing

    errors: list = []   # Initialise an empty list to collect any validation errors

    # ── 2. Validate email ────────────────────────────────────────────
    # RFC-5321 simplified pattern:
    #   - local part: alphanumeric chars + selected special chars (. _ + -)
    #   - @ symbol (exactly one)
    #   - domain: alphanumeric + hyphens, one or more dot-separated labels
    #   - TLD: 2–6 alphabetic characters
    email_pattern: str = r"^[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)*\.[a-zA-Z]{2,6}$"

    email_valid: bool = bool(re.match(email_pattern, email))   # True if pattern matches

    if not email_valid:          # If the email failed, record an error message
        errors.append(f"Invalid email address: '{email}'")


    # ── 3. Validate phone ────────────────────────────────────────────
    # Accepted formats:
    #   - Optional leading '+' (international prefix)
    #   - Digits, spaces, hyphens, and parentheses are allowed separators
    #   - Total digit count must be between 7 and 15 (ITU-T E.164)
    phone_pattern: str = r"^\+?[\d\s\-().]{7,20}$"   # Loose structural check

    # Extract only the digit characters to verify the digit count independently
    digits_only: str = re.sub(r"\D", "", phone)       # Remove every non-digit character

    # A valid phone: matches the structural pattern AND has 7–15 actual digits
    phone_valid: bool = (
        bool(re.match(phone_pattern, phone))  # Structure is acceptable
        and 7 <= len(digits_only) <= 15       # Digit count is within ITU-T range
    )

    if not phone_valid:          # If the phone failed, record an error message
        errors.append(f"Invalid phone number: '{phone}'")


    # ── 4. Compute overall result ─────────────────────────────────────
    is_valid: bool = email_valid and phone_valid   # Both must pass for the record to be valid


    # ── 5. Build and return the output dict ───────────────────────────
    return {
        "is_valid":    is_valid,      # Overall pass/fail
        "email_valid": email_valid,   # Email-specific result
        "phone_valid": phone_valid,   # Phone-specific result
        "errors":      errors         # List of human-readable problems (empty when valid)
    }


# ──────────────────────────────────────────────
# TEST CASES
# ──────────────────────────────────────────────
TEST_CASES: list = [
    # ── Test 1: both fields valid ──────────────────────────────────
    {
        "description": "Valid email and valid international phone",
        "input": {
            "email": "bijay.algo@example.com",   # Well-formed email with dot in local part
            "phone": "+977-9801234567"            # Nepali international format
        },
        "expected": {
            "is_valid":    True,
            "email_valid": True,
            "phone_valid": True,
            "errors":      []
        }
    },

    # ── Test 2: invalid email, valid phone ─────────────────────────
    {
        "description": "Malformed email (missing '@') with a valid phone",
        "input": {
            "email": "not-an-email.com",   # Missing '@' — will fail the regex
            "phone": "9841000111"          # 10-digit local Nepali number — valid
        },
        "expected": {
            "is_valid":    False,
            "email_valid": False,
            "phone_valid": True,
            "errors":      ["Invalid email address: 'not-an-email.com'"]
        }
    },

    # ── Test 3: valid email, invalid phone ─────────────────────────
    {
        "description": "Valid email with a phone number that is too short",
        "input": {
            "email": "user+tag@domain.io",   # Plus-addressing is valid
            "phone": "123"                   # Only 3 digits — below the 7-digit minimum
        },
        "expected": {
            "is_valid":    False,
            "email_valid": True,
            "phone_valid": False,
            "errors":      ["Invalid phone number: '123'"]
        }
    }
]


def run_tests() -> None:
    """
    Iterates over TEST_CASES, calls handle() for each, and prints
    a pass/fail summary comparing actual output to expected output.
    """
    print("=" * 55)
    print("  PyGene Week 1 — Data Validator Test Suite")
    print("=" * 55)

    passed: int = 0   # Counter for tests that match expected output

    for idx, case in enumerate(TEST_CASES, start=1):   # 1-indexed for readability
        description: str  = case["description"]
        input_data:  dict = case["input"]
        expected:    dict = case["expected"]

        actual: dict = handle(input_data)   # Run the validator with the test input

        # Compare actual output to expected output
        test_passed: bool = actual == expected

        # Increment counter only when the test passes
        if test_passed:
            passed += 1

        # Print a human-readable result for each test
        status: str = "PASS ✓" if test_passed else "FAIL ✗"
        print(f"\nTest {idx}: {status}")
        print(f"  Description : {description}")
        print(f"  Input       : {json.dumps(input_data)}")
        print(f"  Expected    : {json.dumps(expected)}")
        print(f"  Got         : {json.dumps(actual)}")

        # On failure, show which keys differ
        if not test_passed:
            for key in expected:
                if expected[key] != actual.get(key):
                    print(f"  MISMATCH on '{key}': expected {expected[key]!r}, got {actual.get(key)!r}")

    # Final summary line
    print("\n" + "=" * 55)
    print(f"  Results: {passed}/{len(TEST_CASES)} tests passed")
    print("=" * 55)


# ──────────────────────────────────────────────
# ENTRY POINT
# Runs the test suite when the script is executed directly.
# ──────────────────────────────────────────────
if __name__ == "__main__":
    run_tests()   # Execute test suite on direct invocation
