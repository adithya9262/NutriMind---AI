from __future__ import annotations

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher

_password_hash = PasswordHash([Argon2Hasher()])


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("password must not be empty")
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _password_hash.verify(plain_password, hashed_password)
    except UnknownHashError:
        return False
