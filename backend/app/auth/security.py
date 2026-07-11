from __future__ import annotations

from passlib.context import CryptContext

# Prefer pbkdf2_sha256 for stable cross-platform local development.
# Keep bcrypt in the context so existing bcrypt hashes remain verifiable.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password, scheme="pbkdf2_sha256")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
