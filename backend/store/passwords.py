"""Password hashing.

Argon2 with the library defaults. Verifying a password that was never set must cost the same
as verifying a real one, so an attacker cannot tell which usernames exist by timing.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_hasher = PasswordHasher()

# used to burn the same time when the username does not exist
_DUMMY_HASH = _hasher.hash("no-such-user")


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(stored_hash: str | None, plain: str) -> bool:
    try:
        return _hasher.verify(stored_hash or _DUMMY_HASH, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
