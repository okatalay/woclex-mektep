import os
from pathlib import Path

from dotenv_min import load_env

load_env(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.environ["DATABASE_URL"]
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_HOURS = 24 * 14
COOKIE_NAME = "mk_session"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
UPLOADS_DIR = DATA_DIR / "uploads"

# Katılım/davet linkleri için genel taban adres (öğrenci sınıf kodu, veli daveti)
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "http://localhost:5195")
