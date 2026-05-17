"""Authentication helpers for the Inventory MVP backend."""

import base64
import hashlib
import hmac
import os

_HASH_NAME = "sha256"
_ITERATIONS = 600_000
_SALT_BYTES = 16


def hash_pin(pin: str) -> str:
    """Return a salted PBKDF2 hash for a raw PIN."""
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(_HASH_NAME, pin.encode("utf-8"), salt, _ITERATIONS)
    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_digest = base64.b64encode(digest).decode("ascii")
    return f"pbkdf2_{_HASH_NAME}${_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Return True when a raw PIN matches a stored PIN hash."""
    try:
        algorithm, iteration_text, encoded_salt, encoded_digest = pin_hash.split("$", 3)
        if not algorithm.startswith("pbkdf2_"):
            return False
        hash_name = algorithm.removeprefix("pbkdf2_")
        iterations = int(iteration_text)
        salt = base64.b64decode(encoded_salt.encode("ascii"))
        expected_digest = base64.b64decode(encoded_digest.encode("ascii"))
    except (ValueError, TypeError):
        return False

    try:
        digest = hashlib.pbkdf2_hmac(hash_name, pin.encode("utf-8"), salt, iterations)
    except ValueError:
        return False
    return hmac.compare_digest(digest, expected_digest)
