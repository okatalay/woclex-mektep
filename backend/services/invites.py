"""Veli davet linki: tek kullanımlık, süreli, hash'lenerek saklanan token."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

GUARDIAN_INVITE_DAYS = 7


def generate_token() -> tuple[str, str]:
    """(ham_token, hash) döner. Ham token yalnız oluşturma anında görünür; DB'de hash tutulur."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def guardian_invite_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=GUARDIAN_INVITE_DAYS)
