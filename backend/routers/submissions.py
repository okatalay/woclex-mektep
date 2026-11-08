import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import Assignment, AssignmentTarget, GuardianLink, Review, Submission, SubmissionFile, User
from services.access import can_manage_classroom
from services.storage import delete_file, resolve_path, save_submission_file
from routers.classes import _get_owned_classroom

router = APIRouter(tags=["submissions"])


def _review_payload(review: Review) -> dict:
    return {
        "id": str(review.id), "score": review.score, "feedback_text": review.feedback_text,
        "request_redo": review.request_redo, "created_at": review.created_at.isoformat(),
    }


def _submission_payload(s: Submission, files: list[SubmissionFile] = None, reviews: list[Review] = None) -> dict:
    out = {
        "id": str(s.id),
        "assignment_id": str(s.assignment_id),
        "student_id": str(s.student_id),
        "status": s.status,
        "text_content": s.text_content,
        "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
    }
    if files is not None:
        out["files"] = [
            {"id": str(f.id), "kind": f.kind, "original_name": f.original_name, "url": f"/api/submissions/files/{f.id}"}
            for f in files
        ]
    if reviews is not None:
        # `reviews`: eskiden yeniye tüm geri bildirim geçmişi. `review`: geriye dönük uyumluluk için en son olan.
        out["reviews"] = [_review_payload(r) for r in reviews]
        out["review"] = out["reviews"][-1] if reviews else None
    return out


def _get_reviews(db: Session, submission_id: uuid.UUID) -> list[Review]:
    return db.scalars(select(Review).where(Review.submission_id == submission_id)
                       .order_by(Review.created_at.asc())).all()


def _get_own_submission(db: Session, ctx: Ctx, assignment_id: uuid.UUID) -> tuple[Assignment, Submission]:
    a = db.get(Assignment, assignment_id)
    target = a and db.scalar(select(AssignmentTarget.id).where(
        AssignmentTarget.assignment_id == a.id, AssignmentTarget.student_id == ctx.user.id))
    if not a or not target:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    s = db.scalar(select(Submission).where(Submission.assignment_id == a.id, Submission.student_id == ctx.user.id))
    if not s:
        raise HTTPException(status_code=404, detail="submission_not_found")
    return a, s


@router.post("/api/me/assignments/{assignment_id}/submit", status_code=200)
def submit(assignment_id: uuid.UUID, request: Request,
           text_content: str | None = Form(default=None),
           files: list[UploadFile] = File(default=[]),
           ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    a, s = _get_own_submission(db, ctx, assignment_id)
    if s.status == "incelendi":
        raise HTTPException(status_code=422, detail="already_reviewed")
    allowed = set(a.submission_types.split(","))

    if text_content and "text" not in allowed:
        raise HTTPException(status_code=422, detail="text_not_allowed")
    if files and not (allowed & {"audio", "file", "image"}):
        raise HTTPException(status_code=422, detail="file_not_allowed")
    if not text_content and not files:
        raise HTTPException(status_code=422, detail="empty_submission")

    if text_content is not None:
        s.text_content = text_content.strip() or None
    for f in files:
        if not f.filename:
            continue
        rel, kind = save_submission_file(s.id, f)
        db.add(SubmissionFile(submission_id=s.id, kind=kind, path=rel, original_name=f.filename))

    s.status = "teslim_edildi"
    s.submitted_at = datetime.now(timezone.utc)
    audit.log(db, ctx.user, request, "submission_submit", "submission", s.id)
    db.commit()

    stored_files = db.scalars(select(SubmissionFile).where(SubmissionFile.submission_id == s.id)).all()
    return _submission_payload(s, files=stored_files)


@router.delete("/api/me/assignments/{assignment_id}/files/{file_id}")
def delete_own_submission_file(assignment_id: uuid.UUID, file_id: uuid.UUID, request: Request,
                                ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    a, s = _get_own_submission(db, ctx, assignment_id)
    if s.status == "incelendi":
        raise HTTPException(status_code=422, detail="already_reviewed")
    f = db.get(SubmissionFile, file_id)
    if not f or f.submission_id != s.id:
        raise HTTPException(status_code=404, detail="file_not_found")
    delete_file(f.path)
    db.delete(f)
    audit.log(db, ctx.user, request, "submission_file_delete", "submission", s.id)
    db.commit()
    stored_files = db.scalars(select(SubmissionFile).where(SubmissionFile.submission_id == s.id)).all()
    return _submission_payload(s, files=stored_files)


@router.get("/api/me/assignments/{assignment_id}/submission")
def get_my_submission(assignment_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    a, s = _get_own_submission(db, ctx, assignment_id)
    stored_files = db.scalars(select(SubmissionFile).where(SubmissionFile.submission_id == s.id)).all()
    reviews = _get_reviews(db, s.id)
    return _submission_payload(s, files=stored_files, reviews=reviews)


@router.get("/api/submissions/{submission_id}")
def get_submission(submission_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    s = db.get(Submission, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="submission_not_found")
    a = db.get(Assignment, s.assignment_id)
    is_teacher_side = a is not None and a.org_id == ctx.org.id
    if is_teacher_side:
        from models import Classroom
        classroom = db.get(Classroom, a.classroom_id)
        if not classroom or not can_manage_classroom(ctx, classroom):
            is_teacher_side = False
    is_owner = s.student_id == ctx.user.id
    is_guardian = db.scalar(select(GuardianLink.id).where(
        GuardianLink.student_id == s.student_id, GuardianLink.guardian_id == ctx.user.id)) is not None
    if not (is_teacher_side or is_owner or is_guardian):
        raise HTTPException(status_code=404, detail="submission_not_found")

    stored_files = db.scalars(select(SubmissionFile).where(SubmissionFile.submission_id == s.id)).all()
    reviews = _get_reviews(db, s.id)
    return _submission_payload(s, files=stored_files, reviews=reviews)


@router.get("/api/submissions/files/{file_id}")
def get_submission_file(file_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    f = db.get(SubmissionFile, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="not_found")
    s = db.get(Submission, f.submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="not_found")
    a = db.get(Assignment, s.assignment_id)
    is_teacher_side = False
    if a and a.org_id == ctx.org.id:
        from models import Classroom
        classroom = db.get(Classroom, a.classroom_id)
        is_teacher_side = bool(classroom and can_manage_classroom(ctx, classroom))
    is_owner = s.student_id == ctx.user.id
    is_guardian = db.scalar(select(GuardianLink.id).where(
        GuardianLink.student_id == s.student_id, GuardianLink.guardian_id == ctx.user.id)) is not None
    if not (is_teacher_side or is_owner or is_guardian):
        raise HTTPException(status_code=404, detail="not_found")
    path = resolve_path(f.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="not_found")
    return FileResponse(path, filename=f.original_name or path.name)


class ReviewBody(BaseModel):
    score: int | None = Field(default=None, ge=1, le=5)
    feedback_text: str | None = Field(default=None, max_length=4000)
    request_redo: bool = False


@router.post("/api/submissions/{submission_id}/review", status_code=201)
def review_submission(submission_id: uuid.UUID, body: ReviewBody, request: Request,
                       ctx: Ctx = Depends(require_perm("submission.review")), db: Session = Depends(get_db)):
    s = db.get(Submission, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail="submission_not_found")
    a = db.get(Assignment, s.assignment_id)
    from models import Classroom
    classroom = a and db.get(Classroom, a.classroom_id)
    if not a or a.org_id != ctx.org.id or not classroom or not can_manage_classroom(ctx, classroom):
        raise HTTPException(status_code=404, detail="submission_not_found")
    if s.status == "bekliyor":
        raise HTTPException(status_code=422, detail="not_submitted")

    review = Review(
        submission_id=s.id, teacher_id=ctx.user.id, score=body.score,
        feedback_text=(body.feedback_text or "").strip() or None, request_redo=body.request_redo,
    )
    db.add(review)
    s.status = "tekrar_istendi" if body.request_redo else "incelendi"
    audit.log(db, ctx.user, request, "submission_review", "submission", s.id, after={"score": body.score})
    db.commit()
    stored_files = db.scalars(select(SubmissionFile).where(SubmissionFile.submission_id == s.id)).all()
    return _submission_payload(s, files=stored_files, reviews=_get_reviews(db, s.id))
