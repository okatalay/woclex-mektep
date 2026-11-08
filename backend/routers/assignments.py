import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import Assignment, AssignmentAttachment, AssignmentTarget, Enrollment, Submission, User
from services.access import can_manage_classroom
from services.storage import delete_file, save_file
from routers.classes import _get_owned_classroom

router = APIRouter(tags=["assignments"])

VALID_TYPES = {"audio", "text", "file"}


def _attachment_payload(f: AssignmentAttachment) -> dict:
    return {"id": str(f.id), "kind": f.kind, "original_name": f.original_name,
            "url": f"/api/assignments/attachments/{f.id}"}


def _assignment_payload(a: Assignment, target_count: int = None, submitted_count: int = None,
                         reviewed_count: int = None, attachments: list[AssignmentAttachment] = None) -> dict:
    out = {
        "id": str(a.id),
        "classroom_id": str(a.classroom_id),
        "title": a.title,
        "description": a.description,
        "submission_types": a.submission_types.split(","),
        "due_at": a.due_at.isoformat() if a.due_at else None,
        "created_at": a.created_at.isoformat(),
    }
    if target_count is not None:
        out["target_count"] = target_count
    if submitted_count is not None:
        out["submitted_count"] = submitted_count
    if reviewed_count is not None:
        out["reviewed_count"] = reviewed_count
    if attachments is not None:
        out["attachments"] = [_attachment_payload(f) for f in attachments]
    return out


def _assignment_attachments(db: Session, assignment_id: uuid.UUID) -> list[AssignmentAttachment]:
    return db.scalars(select(AssignmentAttachment).where(
        AssignmentAttachment.assignment_id == assignment_id).order_by(AssignmentAttachment.created_at)).all()


def _get_assignment_for_teacher(db: Session, ctx: Ctx, assignment_id: uuid.UUID) -> Assignment:
    a = db.get(Assignment, assignment_id)
    if not a or a.org_id != ctx.org.id:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    classroom = _get_owned_classroom(db, ctx, a.classroom_id)
    return a


class CreateAssignmentBody(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    submission_types: list[str] = Field(default_factory=lambda: ["audio", "text", "file"])
    due_at: datetime | None = None
    student_ids: list[uuid.UUID] | None = None


def create_assignment_row(db: Session, ctx: Ctx, classroom, title: str, description: str | None,
                           submission_types: list[str], due_at=None,
                           student_ids: list[uuid.UUID] | None = None) -> tuple[Assignment, int]:
    """Ödev oluşturur ve hedef öğrencileri belirler. `student_ids` verilmezse sınıftaki aktif öğrencilerin hepsi
    hedeflenir; verilirse yalnızca sınıfta aktif kaydı olan öğrenciler arasından seçilenler hedeflenir.
    Diğer router'lar (routes.py, library.py) da kullanır."""
    types = [t for t in submission_types if t in VALID_TYPES]
    if not types:
        raise HTTPException(status_code=422, detail="invalid_submission_types")

    a = Assignment(
        org_id=ctx.org.id, classroom_id=classroom.id, created_by=ctx.user.id,
        title=title.strip(), description=(description or "").strip() or None,
        submission_types=",".join(types), due_at=due_at,
    )
    db.add(a)
    db.flush()

    active_students = set(db.scalars(select(Enrollment.student_id).where(
        Enrollment.classroom_id == classroom.id, Enrollment.status == "active",
    )).all())
    if student_ids is None:
        students = active_students
    else:
        students = active_students & set(student_ids)
        if not students:
            raise HTTPException(status_code=422, detail="no_valid_students")
    for sid in students:
        db.add(AssignmentTarget(assignment_id=a.id, student_id=sid))
        db.add(Submission(assignment_id=a.id, student_id=sid, status="bekliyor"))
    return a, len(students)


@router.post("/api/classes/{classroom_id}/assignments", status_code=201)
def create_assignment(classroom_id: uuid.UUID, body: CreateAssignmentBody, request: Request,
                       ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    a, target_count = create_assignment_row(db, ctx, classroom, body.title, body.description, body.submission_types,
                                             body.due_at, body.student_ids)
    audit.log(db, ctx.user, request, "assignment_create", "assignment", a.id, after={"title": a.title})
    db.commit()
    return _assignment_payload(a, target_count=target_count, submitted_count=0, reviewed_count=0, attachments=[])


@router.post("/api/assignments/{assignment_id}/attachments", status_code=201)
def add_assignment_attachment(assignment_id: uuid.UUID, request: Request,
                               files: list[UploadFile] = File(...),
                               ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    a = _get_assignment_for_teacher(db, ctx, assignment_id)
    added = []
    for f in files:
        if not f.filename:
            continue
        rel, kind = save_file("assignment-materials", a.id, f)
        att = AssignmentAttachment(assignment_id=a.id, kind=kind, path=rel, original_name=f.filename)
        db.add(att)
        added.append(att)
    audit.log(db, ctx.user, request, "assignment_attachment_add", "assignment", a.id, after={"count": len(added)})
    db.commit()
    return [_attachment_payload(f) for f in added]


class FromArchiveBody(BaseModel):
    item_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


@router.post("/api/assignments/{assignment_id}/attachments/from-archive", status_code=201)
def add_attachments_from_archive(assignment_id: uuid.UUID, body: FromArchiveBody, request: Request,
                                  ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    """Arşiv içeriklerinin dosyalarını ödev materyaline kopyalar."""
    from models import LibraryItem, LibraryItemFile
    from services.storage import copy_file

    a = _get_assignment_for_teacher(db, ctx, assignment_id)
    added = []
    for iid in body.item_ids:
        item = db.get(LibraryItem, iid)
        if not item or item.org_id != ctx.org.id:
            raise HTTPException(status_code=404, detail="library_item_not_found")
        for f in db.scalars(select(LibraryItemFile).where(LibraryItemFile.library_item_id == item.id)
                             .order_by(LibraryItemFile.created_at)).all():
            att = AssignmentAttachment(assignment_id=a.id, kind=f.kind, original_name=f.original_name,
                                       path=copy_file(f.path, "assignment-materials", a.id))
            db.add(att)
            added.append(att)
    audit.log(db, ctx.user, request, "assignment_attachment_from_archive", "assignment", a.id,
              after={"count": len(added)})
    db.commit()
    return [_attachment_payload(f) for f in added]


@router.delete("/api/assignments/{assignment_id}/attachments/{attachment_id}")
def delete_assignment_attachment(assignment_id: uuid.UUID, attachment_id: uuid.UUID, request: Request,
                                  ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    a = _get_assignment_for_teacher(db, ctx, assignment_id)
    att = db.get(AssignmentAttachment, attachment_id)
    if not att or att.assignment_id != a.id:
        raise HTTPException(status_code=404, detail="attachment_not_found")
    delete_file(att.path)
    db.delete(att)
    audit.log(db, ctx.user, request, "assignment_attachment_delete", "assignment", a.id)
    db.commit()
    return {"ok": True}


@router.get("/api/assignments/attachments/{attachment_id}")
def get_assignment_attachment(attachment_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    from services.storage import resolve_path

    att = db.get(AssignmentAttachment, attachment_id)
    if not att:
        raise HTTPException(status_code=404, detail="not_found")
    a = db.get(Assignment, att.assignment_id)
    if not a or a.org_id != ctx.org.id:
        raise HTTPException(status_code=404, detail="not_found")
    from models import Classroom
    classroom = db.get(Classroom, a.classroom_id)
    is_teacher_side = bool(classroom and can_manage_classroom(ctx, classroom))
    is_target = db.scalar(select(AssignmentTarget.id).where(
        AssignmentTarget.assignment_id == a.id, AssignmentTarget.student_id == ctx.user.id)) is not None
    if not (is_teacher_side or is_target):
        raise HTTPException(status_code=404, detail="not_found")
    path = resolve_path(att.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="not_found")
    return FileResponse(path, filename=att.original_name or path.name)


@router.get("/api/classes/{classroom_id}/assignments")
def list_assignments(classroom_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    rows = db.scalars(select(Assignment).where(Assignment.classroom_id == classroom.id)
                       .order_by(Assignment.created_at.desc())).all()
    out = []
    for a in rows:
        all_ids = db.scalars(select(Submission.status).where(Submission.assignment_id == a.id)).all()
        target_count = len(all_ids)
        submitted_count = sum(1 for st in all_ids if st != "bekliyor")
        reviewed_count = sum(1 for st in all_ids if st == "incelendi")
        out.append(_assignment_payload(a, target_count, submitted_count, reviewed_count))
    return out


@router.get("/api/assignments/{assignment_id}")
def get_assignment(assignment_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    a = _get_assignment_for_teacher(db, ctx, assignment_id)
    rows = db.execute(
        select(Submission, User)
        .join(User, User.id == Submission.student_id)
        .where(Submission.assignment_id == a.id)
        .order_by(User.full_name)
    ).all()
    submissions = [
        {
            "submission_id": str(s.id), "student_id": str(u.id), "full_name": u.full_name,
            "status": s.status, "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
        }
        for s, u in rows
    ]
    payload = _assignment_payload(a, attachments=_assignment_attachments(db, a.id))
    payload["submissions"] = submissions
    return payload


@router.get("/api/me/assignments")
def my_assignments(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Assignment, Submission)
        .join(Submission, (Submission.assignment_id == Assignment.id) & (Submission.student_id == ctx.user.id))
        .where(Assignment.id.in_(select(AssignmentTarget.assignment_id).where(AssignmentTarget.student_id == ctx.user.id)))
        .order_by(Assignment.created_at.desc())
    ).all()
    out = []
    for a, s in rows:
        p = _assignment_payload(a)
        p["submission"] = {"id": str(s.id), "status": s.status, "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None}
        out.append(p)
    return out


@router.get("/api/me/assignments/{assignment_id}")
def my_assignment_detail(assignment_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    target = a and db.scalar(select(AssignmentTarget.id).where(
        AssignmentTarget.assignment_id == a.id, AssignmentTarget.student_id == ctx.user.id))
    if not a or not target:
        raise HTTPException(status_code=404, detail="assignment_not_found")
    return _assignment_payload(a, attachments=_assignment_attachments(db, a.id))
