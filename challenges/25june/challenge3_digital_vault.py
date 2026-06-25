"""
Digital Vault Security System
Challenge 3

Console-based secure note manager with user authentication, password hashing,
account lockout, session timeout, and per-user data isolation.
"""

import getpass
import hashlib
import hmac
import json
import os
import re
import time


VAULT_FILE = "vault_data.json"
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = 300          # 5 minutes in seconds
SESSION_TIMEOUT = 120           # 2 minutes in seconds
SALT_LENGTH = 32                # bytes


def _hash_password(password: str, salt: bytes) -> str:
    """
    Derive a SHA-256 HMAC of the password using the provided salt.

    HMAC is used over raw SHA-256 to bind the hash to a key, making
    length-extension attacks irrelevant and providing a standard KDF interface.
    """
    return hmac.new(salt, password.encode("utf-8"), hashlib.sha256).hexdigest()


def _generate_salt() -> bytes:
    return os.urandom(SALT_LENGTH)


def _verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    salt = bytes.fromhex(salt_hex)
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


def _xor_cipher(text: str, key: str) -> str:
    """
    Symmetric XOR cipher for note content encryption.

    Key is cycled across the text. Output is hex-encoded to remain JSON-safe.
    This provides basic obfuscation. For production, use AES-GCM via the
    `cryptography` library.
    """
    key_bytes = key.encode("utf-8")
    text_bytes = text.encode("utf-8")
    encrypted = bytes(
        b ^ key_bytes[i % len(key_bytes)]
        for i, b in enumerate(text_bytes)
    )
    return encrypted.hex()


def _xor_decipher(hex_text: str, key: str) -> str:
    key_bytes = key.encode("utf-8")
    encrypted = bytes.fromhex(hex_text)
    decrypted = bytes(
        b ^ key_bytes[i % len(key_bytes)]
        for i, b in enumerate(encrypted)
    )
    return decrypted.decode("utf-8")


PASSWORD_PATTERN = re.compile(
    r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$'
)


def validate_password(password: str) -> list[str]:
    """
    Return a list of unmet password requirements.
    An empty list means the password is acceptable.
    """
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r'[A-Z]', password):
        errors.append("at least one uppercase letter")
    if not re.search(r'[a-z]', password):
        errors.append("at least one lowercase letter")
    if not re.search(r'\d', password):
        errors.append("at least one digit")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append("at least one special character")
    return errors


def load_vault() -> dict:
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_vault(users: dict) -> None:
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not persist vault data: {e}")


def register(users: dict) -> None:
    print("\n--- REGISTRATION ---")
    username = input("Enter username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    if not re.match(r'^[a-zA-Z0-9_]{3,30}$', username):
        print("Username must be 3-30 characters: letters, digits, and underscores only.")
        return

    if username in users:
        print("Username already exists.")
        return

    password = getpass.getpass("Enter password: ")
    errors = validate_password(password)
    if errors:
        print("Password does not meet requirements:")
        for e in errors:
            print(f"  - {e}")
        return

    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        return

    salt = _generate_salt()
    users[username] = {
        "password_hash": _hash_password(password, salt),
        "salt": salt.hex(),
        "failed_attempts": 0,
        "locked": False,
        "locked_at": None,
        "notes": [],
    }
    save_vault(users)
    print("Registration successful.")


def attempt_login(users: dict) -> tuple[str, dict] | tuple[None, None]:
    """
    Validate credentials and return (username, user_record) on success,
    or (None, None) on failure. Manages lockout state internally.
    """
    print("\n--- LOGIN ---")
    username = input("Enter username: ").strip()

    if username not in users:
        print("Invalid username or password.")
        return None, None

    user = users[username]

    if user["locked"]:
        elapsed = time.time() - (user["locked_at"] or 0)
        if elapsed < LOCKOUT_DURATION:
            remaining = int(LOCKOUT_DURATION - elapsed)
            print(f"Account locked. Try again in {remaining} seconds.")
            return None, None
        else:
            user["locked"] = False
            user["failed_attempts"] = 0
            user["locked_at"] = None

    password = getpass.getpass("Enter password: ")

    if not _verify_password(password, user["password_hash"], user["salt"]):
        user["failed_attempts"] += 1
        remaining_attempts = MAX_FAILED_ATTEMPTS - user["failed_attempts"]

        if user["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
            user["locked"] = True
            user["locked_at"] = time.time()
            save_vault(users)
            print("Account locked due to 3 failed attempts. Try after 5 minutes.")
        else:
            save_vault(users)
            print(f"Incorrect password. Attempts left: {remaining_attempts}")

        return None, None

    user["failed_attempts"] = 0
    save_vault(users)
    print("Login successful.")
    return username, user


def check_session_timeout(last_active: float) -> bool:
    """Return True if the session has timed out."""
    return (time.time() - last_active) > SESSION_TIMEOUT


def view_notes(user: dict, encryption_key: str) -> None:
    notes = user.get("notes", [])
    if not notes:
        print("\nNo notes stored.")
        return

    print("\n--- YOUR NOTES ---")
    for i, note in enumerate(notes, 1):
        content = _xor_decipher(note["content"], encryption_key)
        created = time.strftime("%Y-%m-%d %H:%M", time.localtime(note["created_at"]))
        print(f"\n[{i}] {note['title']}  (added: {created})")
        print(f"    {content}")


def add_note(user: dict, users: dict, encryption_key: str) -> None:
    print("\n--- ADD NOTE ---")
    title = input("Note title: ").strip()
    if not title:
        print("Title cannot be empty.")
        return

    content = input("Note content: ").strip()
    if not content:
        print("Content cannot be empty.")
        return

    encrypted_content = _xor_cipher(content, encryption_key)
    user["notes"].append({
        "title": title,
        "content": encrypted_content,
        "created_at": time.time(),
    })
    save_vault(users)
    print("Note added successfully.")


def delete_note(user: dict, users: dict, encryption_key: str) -> None:
    notes = user.get("notes", [])
    if not notes:
        print("\nNo notes to delete.")
        return

    view_notes(user, encryption_key)
    raw = input("\nEnter note number to delete (or 0 to cancel): ").strip()

    if not raw.isdigit():
        print("Invalid input.")
        return

    index = int(raw) - 1
    if raw == "0":
        return
    if index < 0 or index >= len(notes):
        print("Note number out of range.")
        return

    removed = notes.pop(index)
    save_vault(users)
    print(f"Note '{removed['title']}' deleted.")


def search_notes(user: dict, encryption_key: str) -> None:
    query = input("Search title: ").strip().lower()
    if not query:
        print("Search query cannot be empty.")
        return

    results = [
        (i + 1, note)
        for i, note in enumerate(user.get("notes", []))
        if query in note["title"].lower()
    ]

    if not results:
        print("No matching notes found.")
        return

    print(f"\nFound {len(results)} result(s):")
    for idx, note in results:
        content = _xor_decipher(note["content"], encryption_key)
        print(f"\n[{idx}] {note['title']}")
        print(f"    {content}")


def export_notes(user: dict, username: str, encryption_key: str) -> None:
    notes = user.get("notes", [])
    if not notes:
        print("No notes to export.")
        return

    filename = f"{username}_notes_export.json"
    export_data = [
        {
            "title": note["title"],
            "content": _xor_decipher(note["content"], encryption_key),
            "created_at": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(note["created_at"])
            ),
        }
        for note in notes
    ]
    try:
        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)
        print(f"Notes exported to {filename}")
    except IOError as e:
        print(f"Export failed: {e}")


def vault_menu(username: str, user: dict, users: dict) -> None:
    """
    Main vault interface for an authenticated user.

    The encryption key is derived from the username so that each user's
    notes are encrypted with a distinct key without requiring extra storage.
    This is a lightweight, demonstrative approach.
    """
    encryption_key = hashlib.sha256(username.encode()).hexdigest()[:16]
    last_active = time.time()

    while True:
        if check_session_timeout(last_active):
            print("\n[Session Timeout] You have been logged out due to inactivity.")
            return

        print("\n--- VAULT MENU ---")
        print("  1. Add note")
        print("  2. View notes")
        print("  3. Search notes")
        print("  4. Delete note")
        print("  5. Export notes")
        print("  6. Logout")
        choice = input("Choose: ").strip()
        last_active = time.time()

        if choice == "1":
            add_note(user, users, encryption_key)
        elif choice == "2":
            view_notes(user, encryption_key)
        elif choice == "3":
            search_notes(user, encryption_key)
        elif choice == "4":
            delete_note(user, users, encryption_key)
        elif choice == "5":
            export_notes(user, username, encryption_key)
        elif choice == "6":
            print("Logged out.")
            return
        else:
            print("Invalid option. Please choose 1-6.")


def main() -> None:
    users = load_vault()

    print("=" * 44)
    print("   DIGITAL VAULT SECURITY SYSTEM")
    print("=" * 44)

    while True:
        print("\n  1. Register")
        print("  2. Login")
        print("  3. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            register(users)
        elif choice == "2":
            username, user = attempt_login(users)
            if username is not None:
                vault_menu(username, user, users)
        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please choose 1-3.")


if __name__ == "__main__":
    main()
