import shutil
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from config import UPLOADS_DIR

MAX_BYTES = 20 * 1024 * 1024

_KIND_EXT = {
    "audio": {".webm", ".mp3", ".m4a", ".wav", ".ogg"},
    "image": {".jpg", ".jpeg", ".png", ".webp", ".heic"},
    "file": {".pdf", ".doc", ".docx", ".txt"},
}


def guess_kind(filename: str) -> str:
    ext = Path(filename or "").suffix.lower()
    for kind, exts in _KIND_EXT.items():
        if ext in exts:
            return kind
    return "file"


def save_file(category: str, owner_id: uuid.UUID, upload: UploadFile) -> tuple[str, str]:
    """Diske kaydeder, (relative_path, kind) döner. 20MB üstünü reddeder."""
    kind = guess_kind(upload.filename or "")
    ext = Path(upload.filename or "").suffix.lower() or ".bin"
    subdir = UPLOADS_DIR / category / str(owner_id)
    subdir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    dest = subdir / name

    size = 0
    with dest.open("wb") as out:
        while chunk := upload.file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="file_too_large")
            out.write(chunk)

    rel = str(dest.relative_to(UPLOADS_DIR))
    return rel, kind


def copy_file(rel_path: str, category: str, owner_id: uuid.UUID) -> str:
    """Var olan dosyanın bağımsız bir kopyasını yeni sahibin klasörüne yazar, yeni relative path döner."""
    src = resolve_path(rel_path)
    if not src.exists():
        raise HTTPException(status_code=404, detail="not_found")
    subdir = UPLOADS_DIR / category / str(owner_id)
    subdir.mkdir(parents=True, exist_ok=True)
    dest = subdir / f"{uuid.uuid4().hex}{src.suffix}"
    shutil.copyfile(src, dest)
    return str(dest.relative_to(UPLOADS_DIR))


def save_submission_file(submission_id: uuid.UUID, upload: UploadFile) -> tuple[str, str]:
    return save_file("submissions", submission_id, upload)


def delete_file(rel_path: str) -> None:
    path = resolve_path(rel_path)
    path.unlink(missing_ok=True)


def resolve_path(rel_path: str) -> Path:
    p = (UPLOADS_DIR / rel_path).resolve()
    if not str(p).startswith(str(UPLOADS_DIR.resolve())):
        raise HTTPException(status_code=404, detail="not_found")
    return p
