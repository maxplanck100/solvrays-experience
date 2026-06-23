# Design Notes — Week 1: Data Validator

## Overview

`data_validator.py` is a stateless, side-effect-free function that accepts a dict
and returns a dict. The design follows the PyGene `handle()` contract: one entry
point, explicit input/output schemas, deterministic behaviour.

---

## Email Validation

### Regex used

```
^[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)*\.[a-zA-Z]{2,6}$
```

### Rationale

Full RFC-5321 compliance via regex is notoriously complex (the "official" RFC
regex spans several hundred characters). This pattern covers the vast majority
of real-world email addresses while remaining readable and maintainable.

**What it allows:**
- Local part: alphanumeric characters, dots, plus signs, hyphens, underscores
- Exactly one `@` symbol
- Domain: one or more dot-separated labels with alphanumerics and hyphens
- TLD: 2–6 alphabetic characters (covers `.io`, `.com`, `.museum`, etc.)

**Known limitations:**
- Does not validate quoted local parts (`"user name"@example.com`)
- Does not validate IP-address domains (`user@[192.168.1.1]`)
- Does not perform DNS/MX record lookup — syntactic only

### Alternatives considered

| Approach | Pros | Cons | Decision |
|---|---|---|---|
| `email-validator` library | RFC-compliant, DNS check | External dependency | Deferred to v2 |
| Full RFC regex | Theoretically complete | 500+ chars, unreadable | Rejected |
| Simple `@` split | Easy to understand | Too permissive | Rejected |
| **Current regex** | Readable, covers 99% of real emails | Misses edge cases | **Chosen** |

---

## Phone Validation

### Approach: two-pass

1. **Structural regex** — allows `+`, digits, spaces, hyphens, parentheses
2. **Digit count check** — extracts only digits and enforces ITU-T E.164 bounds (7–15)

This separates *format acceptability* from *length validity*, making error
messages more precise and the logic easier to unit-test independently.

### ITU-T E.164 bounds

| Bound | Value | Rationale |
|---|---|---|
| Minimum | 7 digits | Shortest valid national numbers (some Pacific islands) |
| Maximum | 15 digits | ITU-T E.164 hard limit |

**Known limitations:**
- Does not validate country codes
- Does not distinguish mobile vs. landline
- Does not handle extension numbers (`ext. 42`)

---

## Output Contract

The function always returns all four keys regardless of outcome. This means
callers can safely access `result["errors"]` without a `KeyError` even on
successful validation — it is simply an empty list.

```python
# Safe — no KeyError, no None check needed
if result["errors"]:
    log.warning(result["errors"])
```

---

## Dependency Decision

The module uses **only the Python standard library** (`re`, `json`). This is a
deliberate constraint for Week 1: zero-install, zero-dependency execution makes
the deliverable portable across any Python 3.8+ environment.
