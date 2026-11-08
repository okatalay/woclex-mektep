import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from deps import Ctx, current_ctx
from models import Assignment, AssignmentTarget, Classroom, Enrollment, GuardianLink, Submission, User
from services.progress import student_progress

router = APIRouter(prefix="/api/guardians", tags=["guardians"])


@router.get("/me/children")
def my_children(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    links = db.execute(
        select(GuardianLink, User)
        .join(User, User.id == GuardianLink.student_id)
        .where(GuardianLink.guardian_id == ctx.user.id)
        .order_by(GuardianLink.created_at)
    ).all()

    out = []
    for link, student in links:
        classrooms = db.execute(
            select(Classroom, User)
            .join(Enrollment, Enrollment.classroom_id == Classroom.id)
            .join(User, User.id == Classroom.teacher_id)
            .where(Enrollment.student_id == student.id, Enrollment.status == "active")
        ).all()
        out.append({
            "student_id": str(student.id),
            "full_name": student.full_name,
            "relation": link.relation,
            "classrooms": [{"id": str(c.id), "name": c.name, "teacher_name": t.full_name} for c, t in classrooms],
            "progress": student_progress(db, student.id),
        })
    return out


@router.get("/children/{student_id}/assignments")
def child_assignments(student_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    linked = db.scalar(select(GuardianLink.id).where(
        GuardianLink.student_id == student_id, GuardianLink.guardian_id == ctx.user.id))
    if not linked:
        raise HTTPException(status_code=404, detail="student_not_found")

    rows = db.execute(
        select(Assignment, Submission)
        .join(Submission, (Submission.assignment_id == Assignment.id) & (Submission.student_id == student_id))
        .where(Assignment.id.in_(select(AssignmentTarget.assignment_id).where(AssignmentTarget.student_id == student_id)))
        .order_by(Assignment.created_at.desc())
    ).all()
    return [
        {
            "id": str(a.id), "title": a.title, "due_at": a.due_at.isoformat() if a.due_at else None,
            "status": s.status, "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "submission_id": str(s.id),
        }
        for a, s in rows
    ]
