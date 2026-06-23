"""
Demonstrates how to import and call data_validator.handle()
in a variety of real-world scenarios.

Run:
    python examples/usage_example.py
"""

import sys
import json
from pathlib import Path

# ── Allow import from parent week1/ directory ────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_validator import handle  # noqa: E402


# ─────────────────────────────────────────────────────────────────────
# 1. SINGLE CALL — inline dict
# ─────────────────────────────────────────────────────────────────────
print("=" * 55)
print("1. Single call — inline dict")
print("=" * 55)

result = handle({"email": "bijay.algo@example.com", "phone": "+977-9801234567"})
print(json.dumps(result, indent=2))


# ─────────────────────────────────────────────────────────────────────
# 2. BATCH PROCESSING — read from a JSON file
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("2. Batch processing — valid_inputs.json")
print("=" * 55)

valid_file = Path(__file__).parent / "valid_inputs.json"
records    = json.loads(valid_file.read_text(encoding="utf-8"))

for rec in records:
    payload = {"email": rec["email"], "phone": rec["phone"]}
    out     = handle(payload)
    status  = "✓ PASS" if out["is_valid"] else "✗ FAIL"
    print(f"  [{rec['_id']}] {status}  —  {rec['_description']}")


# ─────────────────────────────────────────────────────────────────────
# 3. ERROR INSPECTION — invalid inputs
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("3. Error inspection — invalid_inputs.json")
print("=" * 55)

invalid_file = Path(__file__).parent / "invalid_inputs.json"
bad_records  = json.loads(invalid_file.read_text(encoding="utf-8"))

for rec in bad_records:
    payload = {"email": rec["email"], "phone": rec["phone"]}
    out     = handle(payload)
    print(f"\n  [{rec['_id']}] {rec['_description']}")
    print(f"    email_valid : {out['email_valid']}")
    print(f"    phone_valid : {out['phone_valid']}")
    for err in out["errors"]:
        print(f"    ✗ {err}")


# ─────────────────────────────────────────────────────────────────────
# 4. GUARD USAGE — raise on invalid
# ─────────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("4. Guard pattern — raise ValueError on invalid input")
print("=" * 55)

def validate_or_raise(email: str, phone: str) -> dict:
    """Call handle() and raise ValueError if validation fails."""
    result = handle({"email": email, "phone": phone})
    if not result["is_valid"]:
        raise ValueError(f"Validation failed: {result['errors']}")
    return result

try:
    validate_or_raise("good@example.com", "+1-800-555-0199")
    print("  good@example.com  →  passed (no exception)")
except ValueError as exc:
    print(f"  ERROR: {exc}")

try:
    validate_or_raise("bad-email", "123")
    print("  bad-email  →  passed (unexpected)")
except ValueError as exc:
    print(f"  Caught expected error: {exc}")

print()
