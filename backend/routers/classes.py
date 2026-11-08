import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from config import PUBLIC_BASE_URL
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import Classroom, Enrollment, GuardianInvite, GuardianLink, User
from services.access import can_manage_classroom
from services.codes import generate_join_code
from services.invites import generate_token, guardian_invite_expiry
from services.progress import student_progress

router = APIRouter(prefix="/api/classes", tags=["classes"])


def _classroom_payload(c: Classroom) -> dict:
    return {
        "id": str(c.id),
        "name": c.name,
        "join_code": c.join_code,
        "join_enabled": c.join_enabled,
        "is_archived": c.is_archived,
        "join_url": f"{PUBLIC_BASE_URL}/katil/{c.join_code}",
    }


def _get_owned_classroom(db: Session, ctx: Ctx, classroom_id: uuid.UUID) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if not classroom or not can_manage_classroom(ctx, classroom):
        raise HTTPException(status_code=404, detail="classroom_not_found")
    return classroom


def _get_active_enrollment(db: Session, classroom: Classroom, student_id: uuid.UUID) -> Enrollment:
    enrollment = db.scalar(select(Enrollment).where(
        Enrollment.classroom_id == classroom.id, Enrollment.student_id == student_id,
        Enrollment.status == "active",
    ))
    if not enrollment:
        raise HTTPException(status_code=404, detail="student_not_found")
    return enrollment


def _guardians_payload(db: Session, student_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(GuardianLink, User)
        .join(User, User.id == GuardianLink.guardian_id)
        .where(GuardianLink.student_id == student_id)
        .order_by(GuardianLink.created_at)
    ).all()
    return [
        {"guardian_id": str(u.id), "full_name": u.full_name, "username": u.username, "relation": link.relation}
        for link, u in rows
    ]


class CreateClassroomBody(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class UpdateClassroomBody(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    join_enabled: bool | None = None


class GuardianInviteBody(BaseModel):
    relation: str | None = Field(default=None, max_length=40)


@router.post("", status_code=201)
def create_classroom(body: CreateClassroomBody, request: Request,
                      ctx: Ctx = Depends(require_perm("classroom.create")), db: Session = Depends(get_db)):
    code = generate_join_code()
    while db.scalar(select(Classroom.id).where(Classroom.join_code == code)):
        code = generate_join_code()
    classroom = Classroom(org_id=ctx.org.id, teacher_id=ctx.user.id, name=body.name.strip(), join_code=code)
    db.add(classroom)
    db.flush()
    audit.log(db, ctx.user, request, "classroom_create", "classroom", classroom.id, after={"name": classroom.name})
    db.commit()
    return _classroom_payload(classroom)


@router.get("")
def list_classrooms(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    q = select(Classroom).where(Classroom.org_id == ctx.org.id, Classroom.is_archived.is_(False))
    if not ctx.can("classroom.manage_all"):
        q = q.where(Classroom.teacher_id == ctx.user.id)
    rows = db.scalars(q.order_by(Classroom.created_at.desc())).all()
    return [_classroom_payload(c) for c in rows]


@router.get("/{classroom_id}")
def get_classroom(classroom_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    return _classroom_payload(classroom)


@router.patch("/{classroom_id}")
def update_classroom(classroom_id: uuid.UUID, body: UpdateClassroomBody, request: Request,
                      ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    before = {"name": classroom.name, "join_enabled": classroom.join_enabled}
    if body.name is not None:
        classroom.name = body.name.strip()
    if body.join_enabled is not None:
        classroom.join_enabled = body.join_enabled
    audit.log(db, ctx.user, request, "classroom_update", "classroom", classroom.id, before=before,
              after={"name": classroom.name, "join_enabled": classroom.join_enabled})
    db.commit()
    return _classroom_payload(classroom)


@router.post("/{classroom_id}/regenerate-code")
def regenerate_code(classroom_id: uuid.UUID, request: Request,
                     ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    old = classroom.join_code
    code = generate_join_code()
    while db.scalar(select(Classroom.id).where(Classroom.join_code == code)):
        code = generate_join_code()
    classroom.join_code = code
    audit.log(db, ctx.user, request, "classroom_regenerate_code", "classroom", classroom.id,
              before={"join_code": old}, after={"join_code": code})
    db.commit()
    return _classroom_payload(classroom)


@router.get("/{classroom_id}/students")
def list_students(classroom_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    rows = db.execute(
        select(Enrollment, User)
        .join(User, User.id == Enrollment.student_id)
        .where(Enrollment.classroom_id == classroom.id, Enrollment.status == "active")
        .order_by(Enrollment.joined_at.desc())
    ).all()
    return [
        {"student_id": str(u.id), "full_name": u.full_name, "username": u.username,
         "joined_at": e.joined_at.isoformat()}
        for e, u in rows
    ]


@router.get("/{classroom_id}/students/{student_id}")
def get_student(classroom_id: uuid.UUID, student_id: uuid.UUID,
                 ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    enrollment = _get_active_enrollment(db, classroom, student_id)
    student = db.get(User, student_id)
    return {
        "student_id": str(student.id), "full_name": student.full_name, "username": student.username,
        "joined_at": enrollment.joined_at.isoformat(), "guardians": _guardians_payload(db, student_id),
        "progress": student_progress(db, student_id),
    }


@router.post("/{classroom_id}/students/{student_id}/remove")
def remove_student(classroom_id: uuid.UUID, student_id: uuid.UUID, request: Request,
                    ctx: Ctx = Depends(require_perm("student.manage")), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    enrollment = _get_active_enrollment(db, classroom, student_id)
    enrollment.status = "removed"
    audit.log(db, ctx.user, request, "student_remove", "classroom", classroom.id, before={"student_id": str(student_id)})
    db.commit()
    return {"ok": True}


@router.post("/{classroom_id}/students/{student_id}/guardian-invite", status_code=201)
def create_guardian_invite(classroom_id: uuid.UUID, student_id: uuid.UUID, body: GuardianInviteBody, request: Request,
                            ctx: Ctx = Depends(require_perm("student.manage")), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    _get_active_enrollment(db, classroom, student_id)
    token, token_hash = generate_token()
    invite = GuardianInvite(
        token_hash=token_hash, org_id=ctx.org.id, student_id=student_id, created_by=ctx.user.id,
        relation_hint=body.relation, expires_at=guardian_invite_expiry(),
    )
    db.add(invite)
    audit.log(db, ctx.user, request, "guardian_invite_create", "guardian_invite", student_id)
    db.commit()
    return {"token": token, "invite_url": f"{PUBLIC_BASE_URL}/veli/{token}", "expires_at": invite.expires_at.isoformat()}
