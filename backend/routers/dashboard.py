from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from deps import Ctx, current_ctx
from models import Assignment, AssignmentTarget, Classroom, Enrollment, GuardianLink, Submission, User
from services.progress import student_progress

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _teacher_dashboard(ctx: Ctx, db: Session) -> dict:
    q = select(Classroom.id).where(Classroom.org_id == ctx.org.id, Classroom.is_archived.is_(False))
    if not ctx.can("classroom.manage_all"):
        q = q.where(Classroom.teacher_id == ctx.user.id)
    classroom_ids = db.scalars(q).all()

    students_count = 0
    pending_statuses = []
    pending_rows = []
    if classroom_ids:
        students_count = len(db.scalars(
            select(Enrollment.id).where(Enrollment.classroom_id.in_(classroom_ids), Enrollment.status == "active")
        ).all())
        assignment_ids = db.scalars(select(Assignment.id).where(Assignment.classroom_id.in_(classroom_ids))).all()
        if assignment_ids:
            pending_statuses = db.scalars(
                select(Submission.id).where(Submission.assignment_id.in_(assignment_ids), Submission.status == "teslim_edildi")
            ).all()
            pending_rows = db.execute(
                select(Submission, User, Assignment)
                .join(User, User.id == Submission.student_id)
                .join(Assignment, Assignment.id == Submission.assignment_id)
                .where(Submission.assignment_id.in_(assignment_ids), Submission.status == "teslim_edildi")
                .order_by(Submission.submitted_at.desc())
                .limit(5)
            ).all()

    return {
        "role": "teacher",
        "classes_count": len(classroom_ids),
        "students_count": students_count,
        "pending_review_count": len(pending_statuses),
        "recent_pending": [
            {
                "submission_id": str(s.id), "assignment_id": str(a.id), "classroom_id": str(a.classroom_id),
                "student_name": u.full_name, "assignment_title": a.title,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            }
            for s, u, a in pending_rows
        ],
    }


def _student_dashboard(ctx: Ctx, db: Session) -> dict:
    progress = student_progress(db, ctx.user.id)
    rows = db.execute(
        select(Assignment, Submission)
        .join(Submission, (Submission.assignment_id == Assignment.id) & (Submission.student_id == ctx.user.id))
        .where(
            Assignment.id.in_(select(AssignmentTarget.assignment_id).where(AssignmentTarget.student_id == ctx.user.id)),
            Submission.status.in_(["bekliyor", "tekrar_istendi"]),
        )
        .order_by(Assignment.due_at.is_(None), Assignment.due_at.asc(), Assignment.created_at.desc())
        .limit(5)
    ).all()
    return {
        "role": "student",
        "progress": progress,
        "pending_assignments": [
            {"id": str(a.id), "title": a.title, "due_at": a.due_at.isoformat() if a.due_at else None, "status": s.status}
            for a, s in rows
        ],
    }


def _guardian_dashboard(ctx: Ctx, db: Session) -> dict:
    links = db.execute(
        select(GuardianLink, User).join(User, User.id == GuardianLink.student_id)
        .where(GuardianLink.guardian_id == ctx.user.id)
    ).all()
    children = [
        {"student_id": str(u.id), "full_name": u.full_name, "progress": student_progress(db, u.id)}
        for _, u in links
    ]
    return {
        "role": "guardian",
        "children_count": len(children),
        "children": children,
        "redo_requested_total": sum(c["progress"]["redo_requested"] for c in children),
    }


@router.get("")
def dashboard(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    role = ctx.membership.role.system_key
    if role in ("owner", "admin", "teacher"):
        return _teacher_dashboard(ctx, db)
    if role == "guardian":
        return _guardian_dashboard(ctx, db)
    return _student_dashboard(ctx, db)
