from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from config import ACCESS_TOKEN_HOURS, JWT_ALGORITHM, JWT_SECRET_KEY

# Kullanıcı yokken de aynı sürede bcrypt çalışsın (kullanıcı adı sızdırmasın)
_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    return bcrypt.checkpw(password.encode(), (password_hash or _DUMMY_HASH).encode()) and password_hash is not None


def create_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_HOURS)
    return jwt.encode({"sub": user_id, "exp": exp}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
