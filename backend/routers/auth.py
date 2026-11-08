import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from config import ACCESS_TOKEN_HOURS, COOKIE_NAME, COOKIE_SECURE
from database import get_db
from deps import Ctx, current_ctx
from models import Classroom, Enrollment, GuardianInvite, GuardianLink, Organization, Role, User
from security import create_token, verify_password
from services import accounts
from services.invites import hash_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Basit deneme sınırı: IP + kullanıcı adı başına 5 dakikada en çok 8 hatalı deneme.
WINDOW, MAX_FAILS = 300, 8
_fails: dict[str, list[float]] = defaultdict(list)


def _recent(key: str) -> list[float]:
    now = time.time()
    _fails[key] = [t for t in _fails[key] if now - t < WINDOW]
    return _fails[key]


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class RegisterTeacherBody(BaseModel):
    account_type: Literal["individual", "institution"]
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=256)
    full_name: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    organization_name: str | None = Field(default=None, max_length=160)


class RegisterStudentBody(BaseModel):
    join_code: str = Field(min_length=3, max_length=24)
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=256)
    full_name: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)


class RegisterGuardianBody(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=256)
    full_name: str = Field(min_length=2, max_length=120)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)


def me_payload(ctx: Ctx) -> dict:
    return {
        "username": ctx.user.username,
        "full_name": ctx.user.full_name,
        "email": ctx.user.email,
        "phone": ctx.user.phone,
        "avatar_url": ctx.user.avatar_url,
        "organization": {"id": str(ctx.org.id), "name": ctx.org.name, "type": ctx.org.type},
        "role": {"id": str(ctx.membership.role_id), "name": ctx.membership.role.name,
                 "system_key": ctx.membership.role.system_key},
        "permissions": sorted(ctx.perms),
    }


def _set_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        COOKIE_NAME, create_token(str(user.id)), max_age=ACCESS_TOKEN_HOURS * 3600,
        httponly=True, samesite="lax", secure=COOKIE_SECURE, path="/",
    )


def _normalize_code(raw: str) -> str:
    return raw.strip().upper().replace(" ", "")


@router.post("/register", status_code=201)
def register_teacher(body: RegisterTeacherBody, request: Request, response: Response, db: Session = Depends(get_db)):
    """Yeni bir eğitmen kaydı; kendi kurumunu (bireysel ya da kurumsal) açar ve sahibi olur."""
    if body.account_type == "institution" and not (body.organization_name or "").strip():
        raise HTTPException(status_code=422, detail={"organization_name": "required"})
    org_name = (body.organization_name or "").strip() if body.account_type == "institution" else body.full_name
    org, roles = accounts.create_org_with_roles(db, org_name, body.account_type)
    user = accounts.create_user(db, org, roles["owner"], body.username, body.password, body.full_name,
                                body.email, body.phone)
    audit.log(db, user, request, "register_teacher", "organization", org.id, after={"type": body.account_type})
    db.commit()
    _set_cookie(response, user)
    db.refresh(user)
    return me_payload(current_ctx(user, db))


@router.get("/join-info/{code}")
def join_info(code: str, db: Session = Depends(get_db)):
    """Katılım linkine tıklayan öğrencinin kayıt öncesi göreceği önizleme. Kimlik doğrulama gerekmez."""
    classroom = db.scalar(select(Classroom).where(Classroom.join_code == _normalize_code(code)))
    if not classroom or not classroom.join_enabled or classroom.is_archived:
        raise HTTPException(status_code=404, detail="join_code_not_found")
    teacher = db.get(User, classroom.teacher_id)
    return {"classroom_name": classroom.name, "teacher_name": teacher.full_name if teacher else ""}


@router.post("/register-student", status_code=201)
def register_student(body: RegisterStudentBody, request: Request, response: Response, db: Session = Depends(get_db)):
    """Sınıf koduyla öğrenci kaydı; eğitmenin kurumuna öğrenci olarak katılır."""
    classroom = db.scalar(select(Classroom).where(Classroom.join_code == _normalize_code(body.join_code)))
    if not classroom or not classroom.join_enabled or classroom.is_archived:
        raise HTTPException(status_code=404, detail="join_code_not_found")
    org = db.get(Organization, classroom.org_id)
    role = db.scalar(select(Role).where(Role.org_id == classroom.org_id, Role.system_key == "student"))
    user = accounts.create_user(db, org, role, body.username, body.password, body.full_name, body.email, body.phone)
    db.add(Enrollment(classroom_id=classroom.id, student_id=user.id))
    audit.log(db, user, request, "register_student", "classroom", classroom.id)
    db.commit()
    _set_cookie(response, user)
    db.refresh(user)
    return me_payload(current_ctx(user, db))


@router.get("/guardian-invite/{token}")
def guardian_invite_info(token: str, db: Session = Depends(get_db)):
    """Veli davet linkine tıklayınca gösterilecek önizleme. Kimlik doğrulama gerekmez."""
    invite = db.scalar(select(GuardianInvite).where(GuardianInvite.token_hash == hash_token(token)))
    if not invite or invite.used_at or invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="invite_not_found")
    student = db.get(User, invite.student_id)
    return {"student_name": student.full_name if student else ""}


@router.post("/register-guardian", status_code=201)
def register_guardian(body: RegisterGuardianBody, request: Request, response: Response, db: Session = Depends(get_db)):
    """Veli davet linkiyle kayıt; öğrenciyle veli bağı kurar."""
    invite = db.scalar(select(GuardianInvite).where(GuardianInvite.token_hash == hash_token(body.token)))
    if not invite or invite.used_at or invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="invite_not_found")
    org = db.get(Organization, invite.org_id)
    role = db.scalar(select(Role).where(Role.org_id == invite.org_id, Role.system_key == "guardian"))
    user = accounts.create_user(db, org, role, body.username, body.password, body.full_name, body.email, body.phone)
    db.add(GuardianLink(student_id=invite.student_id, guardian_id=user.id, relation=invite.relation_hint))
    invite.used_at = datetime.now(timezone.utc)
    audit.log(db, user, request, "register_guardian", "guardian_link", invite.student_id)
    db.commit()
    _set_cookie(response, user)
    db.refresh(user)
    return me_payload(current_ctx(user, db))


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)):
    username = body.username.strip().lower()
    key = f"{request.client.host if request.client else '-'}|{username}"
    if len(_recent(key)) >= MAX_FAILS:
        raise HTTPException(status_code=429, detail="too_many_attempts")

    user = db.scalar(select(User).where(User.username == username))
    ok = verify_password(body.password, user.password_hash if user else None)
    if not (ok and user and user.is_active):
        _fails[key].append(time.time())
        audit.log(db, None, request, "login_failed", "user", None, after={"username": username})
        db.commit()
        raise HTTPException(status_code=401, detail="invalid_credentials")

    _fails.pop(key, None)
    user.last_login_at = datetime.now(timezone.utc)
    audit.log(db, user, request, "login", "user", user.id)
    db.commit()
    _set_cookie(response, user)
    return me_payload(current_ctx(user, db))


@router.get("/me")
def me(ctx: Ctx = Depends(current_ctx)):
    return me_payload(ctx)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
