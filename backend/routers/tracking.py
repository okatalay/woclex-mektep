import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import AttendanceRecord, Enrollment, GuardianLink, PageLog, User
from services.access import can_manage_student
from services.tracking import student_tracking_summary
from routers.classes import _get_owned_classroom

router = APIRouter(tags=["tracking"])

ATTENDANCE_STATUSES = {"geldi", "gec_geldi", "izinli", "gelmedi", "raporlu"}


def _can_view_student(db: Session, ctx: Ctx, student_id: uuid.UUID) -> bool:
    if ctx.user.id == student_id:
        return True
    if db.scalar(select(GuardianLink.id).where(
            GuardianLink.student_id == student_id, GuardianLink.guardian_id == ctx.user.id)):
        return True
    return can_manage_student(db, ctx, student_id)


# ---------- Yoklama ----------

class AttendanceEntry(BaseModel):
    student_id: uuid.UUID
    status: str


class SaveAttendanceBody(BaseModel):
    date: date
    records: list[AttendanceEntry]


@router.post("/api/classes/{classroom_id}/attendance")
def save_attendance(classroom_id: uuid.UUID, body: SaveAttendanceBody, request: Request,
                     ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    active_students = set(db.scalars(select(Enrollment.student_id).where(
        Enrollment.classroom_id == classroom.id, Enrollment.status == "active")).all())
    saved = 0
    for entry in body.records:
        if entry.student_id not in active_students or entry.status not in ATTENDANCE_STATUSES:
            continue
        row = db.scalar(select(AttendanceRecord).where(
            AttendanceRecord.classroom_id == classroom.id, AttendanceRecord.student_id == entry.student_id,
            AttendanceRecord.date == body.date,
        ))
        if row:
            row.status = entry.status
        else:
            db.add(AttendanceRecord(classroom_id=classroom.id, student_id=entry.student_id, date=body.date,
                                     status=entry.status, created_by=ctx.user.id))
        saved += 1
    audit.log(db, ctx.user, request, "attendance_save", "classroom", classroom.id,
              after={"date": body.date.isoformat(), "count": saved})
    db.commit()
    return {"ok": True, "saved": saved}


@router.get("/api/classes/{classroom_id}/attendance")
def get_attendance(classroom_id: uuid.UUID, date: date,
                    ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    rows = db.execute(
        select(Enrollment, User)
        .join(User, User.id == Enrollment.student_id)
        .where(Enrollment.classroom_id == classroom.id, Enrollment.status == "active")
        .order_by(User.full_name)
    ).all()
    existing = {
        r.student_id: r.status for r in db.scalars(select(AttendanceRecord).where(
            AttendanceRecord.classroom_id == classroom.id, AttendanceRecord.date == date))
    }
    return [
        {"student_id": str(u.id), "full_name": u.full_name, "status": existing.get(e.student_id)}
        for e, u in rows
    ]


@router.get("/api/classes/{classroom_id}/attendance/summary")
def attendance_summary_for_class(classroom_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    rows = db.execute(
        select(Enrollment, User)
        .join(User, User.id == Enrollment.student_id)
        .where(Enrollment.classroom_id == classroom.id, Enrollment.status == "active")
        .order_by(User.full_name)
    ).all()
    out = []
    for e, u in rows:
        statuses = db.scalars(select(AttendanceRecord.status).where(
            AttendanceRecord.classroom_id == classroom.id, AttendanceRecord.student_id == u.id)).all()
        total = len(statuses)
        present = sum(1 for s in statuses if s in ("geldi", "gec_geldi"))
        out.append({
            "student_id": str(u.id), "full_name": u.full_name, "total": total, "present": present,
            "rate_pct": round(present / total * 100) if total else 0,
        })
    return out


# ---------- Kur'an sayfa takibi ----------

class CreatePageLogBody(BaseModel):
    log_date: date
    start_page: int = Field(ge=1, le=604)
    end_page: int = Field(ge=1, le=604)
    note: str | None = Field(default=None, max_length=500)


def _page_log_payload(p: PageLog) -> dict:
    return {"id": str(p.id), "log_date": p.log_date.isoformat(), "start_page": p.start_page,
            "end_page": p.end_page, "note": p.note, "created_at": p.created_at.isoformat()}


@router.post("/api/students/{student_id}/page-logs", status_code=201)
def create_page_log(student_id: uuid.UUID, body: CreatePageLogBody, request: Request,
                     ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    if not can_manage_student(db, ctx, student_id):
        raise HTTPException(status_code=404, detail="student_not_found")
    if body.end_page < body.start_page:
        raise HTTPException(status_code=422, detail="invalid_page_range")
    p = PageLog(org_id=ctx.org.id, student_id=student_id, log_date=body.log_date,
                start_page=body.start_page, end_page=body.end_page, note=body.note, created_by=ctx.user.id)
    db.add(p)
    db.flush()
    audit.log(db, ctx.user, request, "page_log_create", "user", student_id,
              after={"start_page": body.start_page, "end_page": body.end_page})
    db.commit()
    return _page_log_payload(p)


@router.get("/api/students/{student_id}/page-logs")
def list_page_logs(student_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    if not _can_view_student(db, ctx, student_id):
        raise HTTPException(status_code=404, detail="student_not_found")
    rows = db.scalars(select(PageLog).where(PageLog.student_id == student_id).order_by(PageLog.log_date.desc())).all()
    return [_page_log_payload(p) for p in rows]


@router.delete("/api/students/{student_id}/page-logs/{log_id}")
def delete_page_log(student_id: uuid.UUID, log_id: uuid.UUID, request: Request,
                     ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    if not can_manage_student(db, ctx, student_id):
        raise HTTPException(status_code=404, detail="student_not_found")
    p = db.get(PageLog, log_id)
    if not p or p.student_id != student_id:
        raise HTTPException(status_code=404, detail="log_not_found")
    db.delete(p)
    audit.log(db, ctx.user, request, "page_log_delete", "user", student_id)
    db.commit()
    return {"ok": True}


@router.get("/api/me/page-logs")
def list_my_page_logs(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    rows = db.scalars(select(PageLog).where(PageLog.student_id == ctx.user.id).order_by(PageLog.log_date.desc())).all()
    return [_page_log_payload(p) for p in rows]


# ---------- Özet ----------

@router.get("/api/students/{student_id}/tracking-summary")
def tracking_summary(student_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    if not _can_view_student(db, ctx, student_id):
        raise HTTPException(status_code=404, detail="student_not_found")
    return student_tracking_summary(db, ctx.org.id, student_id)


@router.get("/api/me/tracking-summary")
def my_tracking_summary(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    return student_tracking_summary(db, ctx.org.id, ctx.user.id)
