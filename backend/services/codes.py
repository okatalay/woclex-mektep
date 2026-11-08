"""Sınıf katılım kodu üretimi."""
import secrets

# Karışabilecek karakterler (O/0, I/1) çıkarıldı.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_join_code() -> str:
    raw = "".join(secrets.choice(_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"
