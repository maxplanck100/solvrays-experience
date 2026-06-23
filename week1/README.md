# Week 1 — Data Validator Function

> **PyGene Learning Track · solvrays-experience**

A stateless Python function that validates an email address and a phone number,
returning a structured result with per-field flags and human-readable error messages.

---

## Deliverable Summary

| Criterion | Weight | Status |
|---|---|---|
| Function Works | 40% | ✅ |
| `handle()` Contract | 20% | ✅ |
| JSON Schemas | 20% | ✅ |
| Documentation | 20% | ✅ |

---

## Project Structure

```
week1/
├── data_validator.py          # Core module — handle() entry point
│
├── schemas/
│   ├── input_schema.json      # JSON Schema draft-07 for input
│   └── output_schema.json     # JSON Schema draft-07 for output
│
├── tests/
│   ├── __init__.py
│   └── test_data_validator.py # 30+ pytest cases across 7 classes
│
├── examples/
│   ├── valid_inputs.json      # 5 sample valid payloads
│   ├── invalid_inputs.json    # 6 sample invalid payloads
│   └── usage_example.py       # Four usage patterns with runnable demos
│
├── docs/
│   ├── DESIGN.md              # Regex rationale, trade-offs, limitations
│   └── IMPROVEMENTS.md        # Prioritised enhancement backlog
│
├── pytest.ini                 # Test runner configuration
├── requirements.txt           # Pinned dev dependencies
└── CHANGELOG.md               # Version history
```

---

## Quick Start

### 1. Clone and navigate

```bash
git clone https://github.com/<your-handle>/solvrays-experience.git
cd solvrays-experience/week1
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the test suite

```bash
pytest                           # uses pytest.ini config automatically
pytest --cov=data_validator      # with coverage report
```

### 5. Try the usage examples

```bash
python examples/usage_example.py
```

---

## Function API

### `handle(input_data: dict) -> dict`

#### Input

```json
{
  "email": "user@example.com",
  "phone": "+977-9801234567"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string | ✅ | Email address to validate |
| `phone` | string | ✅ | Phone number to validate (local or international) |

#### Output

```json
{
  "is_valid":    true,
  "email_valid": true,
  "phone_valid": true,
  "errors":      []
}
```

| Field | Type | Description |
|---|---|---|
| `is_valid` | boolean | `true` only when both fields pass |
| `email_valid` | boolean | Result of the email check |
| `phone_valid` | boolean | Result of the phone check |
| `errors` | string[] | Human-readable failures; empty on success |

---

## Usage Example

```python
from data_validator import handle

# Valid input
result = handle({"email": "bijay.algo@example.com", "phone": "+977-9801234567"})
print(result)
# {"is_valid": True, "email_valid": True, "phone_valid": True, "errors": []}

# Invalid email
result = handle({"email": "not-an-email", "phone": "+977-9801234567"})
print(result)
# {"is_valid": False, "email_valid": False, "phone_valid": True,
#  "errors": ["Invalid email address: 'not-an-email'"]}
```

---

## Validation Rules

### Email
- Must contain exactly one `@` symbol
- Local part: alphanumeric characters, `.`, `+`, `-`, `_`
- Domain: dot-separated labels, alphanumeric and hyphens
- TLD: 2–6 alphabetic characters
- Validation is syntactic only (no DNS lookup)

### Phone
- Optional leading `+` for country code
- Allowed separators: spaces, hyphens, parentheses
- Digit count must be between **7 and 15** (ITU-T E.164)

---

## Running Tests

```bash
# All tests, verbose
pytest -v

# Specific class
pytest tests/test_data_validator.py::TestValidInputs -v

# With coverage
pytest --cov=data_validator --cov-report=term-missing
```

Expected output: **all tests pass, 0 errors, 0 warnings.**

---

## Design Decisions

See [`docs/DESIGN.md`](docs/DESIGN.md) for the full rationale behind regex
choices, the two-pass phone validation strategy, and the no-dependency constraint.

## Future Improvements

See [`docs/IMPROVEMENTS.md`](docs/IMPROVEMENTS.md) for a prioritised backlog
including DNS verification, `libphonenumber` integration, and a CLI interface.

---

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md).

---

*Part of the [solvrays-experience](../) weekly learning portfolio.*
