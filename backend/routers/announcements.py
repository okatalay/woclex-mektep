import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import Announcement, Classroom, Enrollment, GuardianLink
from routers.classes import _get_owned_classroom

router = APIRouter(tags=["announcements"])


def _payload(a: Announcement, classroom_name: str = None) -> dict:
    out = {"id": str(a.id), "classroom_id": str(a.classroom_id), "body": a.body, "created_at": a.created_at.isoformat()}
    if classroom_name is not None:
        out["classroom_name"] = classroom_name
    return out


class CreateAnnouncementBody(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


@router.post("/api/classes/{classroom_id}/announcements", status_code=201)
def create_announcement(classroom_id: uuid.UUID, body: CreateAnnouncementBody, request: Request,
                         ctx: Ctx = Depends(require_perm("announcement.manage")), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    a = Announcement(org_id=ctx.org.id, classroom_id=classroom.id, teacher_id=ctx.user.id, body=body.body.strip())
    db.add(a)
    audit.log(db, ctx.user, request, "announcement_create", "announcement", classroom.id)
    db.commit()
    return _payload(a)


@router.get("/api/classes/{classroom_id}/announcements")
def list_announcements(classroom_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    rows = db.scalars(select(Announcement).where(Announcement.classroom_id == classroom.id)
                       .order_by(Announcement.created_at.desc())).all()
    return [_payload(a) for a in rows]


@router.get("/api/me/announcements")
def my_announcements(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    student_ids = [ctx.user.id]
    if ctx.membership.role.system_key == "guardian":
        student_ids = db.scalars(select(GuardianLink.student_id).where(GuardianLink.guardian_id == ctx.user.id)).all()
        if not student_ids:
            return []

    classroom_ids = db.scalars(
        select(Enrollment.classroom_id).where(Enrollment.student_id.in_(student_ids), Enrollment.status == "active")
    ).all()
    if not classroom_ids:
        return []

    rows = db.execute(
        select(Announcement, Classroom.name)
        .join(Classroom, Classroom.id == Announcement.classroom_id)
        .where(Announcement.classroom_id.in_(classroom_ids))
        .order_by(Announcement.created_at.desc())
        .limit(20)
    ).all()
    return [_payload(a, name) for a, name in rows]
