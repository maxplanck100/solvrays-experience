# Future Improvements — Week 1: Data Validator

A prioritised backlog of enhancements that would take this module from
"learning deliverable" to "production-grade library component."

---

## Priority 1 — Correctness

### 1.1 DNS/MX Record Verification
Replace syntactic email check with a live DNS lookup to confirm the domain
actually accepts mail.

```python
# Candidate library
pip install dnspython

import dns.resolver

def domain_has_mx(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except dns.exception.DNSException:
        return False
```

**Trade-off:** Adds network I/O, making the function no longer pure/stateless.
Suitable for a registration flow; not suitable for bulk batch processing.

---

### 1.2 libphonenumber Integration
Replace the regex + digit-count heuristic with Google's `phonenumbers` library,
which understands country codes, carrier detection, and number types.

```python
pip install phonenumbers

import phonenumbers

def is_valid_phone(raw: str) -> bool:
    try:
        parsed = phonenumbers.parse(raw, None)
        return phonenumbers.is_valid_number(parsed)
    except phonenumbers.NumberParseException:
        return False
```

**Trade-off:** Adds ~8 MB dependency. Worth it for any user-facing product.

---

## Priority 2 — Robustness

### 2.1 Input Schema Enforcement at Runtime
Use `jsonschema.validate()` to enforce `INPUT_SCHEMA` before any logic runs,
converting schema violations into consistent, structured errors.

```python
from jsonschema import validate, ValidationError

def handle(input_data: dict) -> dict:
    try:
        validate(instance=input_data, schema=INPUT_SCHEMA)
    except ValidationError as exc:
        return {"is_valid": False, "email_valid": False,
                "phone_valid": False, "errors": [exc.message]}
    # ... rest of logic
```

---

### 2.2 Normalisation Before Validation
Strip leading/trailing whitespace and lowercase the email domain before
checking, so `"  User@EXAMPLE.COM  "` is treated the same as `"user@example.com"`.

---

### 2.3 Internationalised Email Support
Handle IDN (Internationalised Domain Names) by encoding with `encodings.idna`
before regex matching, supporting domains like `用户@例子.广告`.

---

## Priority 3 — Observability

### 3.1 Structured Logging
Replace `print()` calls in `run_tests()` with Python's `logging` module,
allowing log level control via environment variable.

```python
import logging
log = logging.getLogger(__name__)
log.debug("Validating email: %s", email)
```

---

### 3.2 Metrics / Telemetry Hook
Add an optional `on_result` callback parameter to `handle()`, allowing callers
to emit metrics (e.g. validation failure rate) without coupling the core
function to any specific metrics backend.

---

## Priority 4 — Developer Experience

### 4.1 CLI Interface
Wrap `handle()` with `argparse` or `click` so the validator can be called
from the terminal without writing a Python script.

```bash
python data_validator.py --email user@example.com --phone +977-9801234567
# → {"is_valid": true, "email_valid": true, "phone_valid": true, "errors": []}
```

---

### 4.2 Type Stub File (`data_validator.pyi`)
Add a `.pyi` stub so IDEs provide accurate autocomplete and mypy performs
static type checking on callers.

---

### 4.3 Pre-commit Hooks
Add `.pre-commit-config.yaml` with `black`, `ruff`, and `mypy` to enforce
style and type safety on every commit automatically.

---

## Priority 5 — Packaging

### 5.1 Make It an Importable Package
Add `__init__.py` and a minimal `pyproject.toml` (PEP 517) so `data_validator`
can be installed via pip from the repo root.

---

## Summary Table

| ID | Enhancement | Effort | Impact |
|---|---|---|---|
| 1.1 | DNS/MX verification | Medium | High |
| 1.2 | libphonenumber | Low | High |
| 2.1 | Runtime schema enforcement | Low | Medium |
| 2.2 | Input normalisation | Low | Medium |
| 2.3 | IDN support | High | Low |
| 3.1 | Structured logging | Low | Medium |
| 3.2 | Metrics hook | Medium | Medium |
| 4.1 | CLI interface | Low | High |
| 4.2 | Type stubs | Low | Low |
| 4.3 | Pre-commit hooks | Low | Medium |
| 5.1 | Pip-installable package | Medium | Medium |
