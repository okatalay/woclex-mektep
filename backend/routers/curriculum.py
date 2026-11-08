import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import CurriculumCategory, CurriculumItem, CurriculumStatus, GuardianLink
from services.access import can_manage_student

router = APIRouter(tags=["curriculum"])

VALID_KINDS = {"ezber", "tecvid"}
VALID_STATUSES = {"-", "calisiyor", "tekrar", "ezberlendi"}


def _check_kind(kind: str) -> str:
    if kind not in VALID_KINDS:
        raise HTTPException(status_code=422, detail="invalid_kind")
    return kind


def _get_category(db: Session, ctx: Ctx, category_id: uuid.UUID) -> CurriculumCategory:
    c = db.get(CurriculumCategory, category_id)
    if not c or c.org_id != ctx.org.id:
        raise HTTPException(status_code=404, detail="category_not_found")
    return c


def _build_chart(db: Session, org_id, kind: str, student_id: uuid.UUID) -> dict:
    categories = db.scalars(
        select(CurriculumCategory).where(CurriculumCategory.org_id == org_id, CurriculumCategory.kind == kind)
        .order_by(CurriculumCategory.order_index)
    ).all()
    out = []
    for cat in categories:
        items = db.scalars(
            select(CurriculumItem).where(CurriculumItem.category_id == cat.id).order_by(CurriculumItem.order_index)
        ).all()
        item_ids = [i.id for i in items]
        statuses = {}
        if item_ids:
            rows = db.scalars(select(CurriculumStatus).where(
                CurriculumStatus.item_id.in_(item_ids), CurriculumStatus.student_id == student_id)).all()
            statuses = {r.item_id: r.status for r in rows}
        out.append({
            "id": str(cat.id), "title": cat.title, "order_index": cat.order_index,
            "items": [
                {"id": str(i.id), "title": i.title, "order_index": i.order_index, "status": statuses.get(i.id, "-")}
                for i in items
            ],
        })
    return {"kind": kind, "categories": out}


class CreateCategoryBody(BaseModel):
    kind: str
    title: str = Field(min_length=2, max_length=160)


@router.post("/api/curriculum/categories", status_code=201)
def create_category(body: CreateCategoryBody, request: Request,
                     ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    kind = _check_kind(body.kind)
    next_index = len(db.scalars(select(CurriculumCategory.id).where(
        CurriculumCategory.org_id == ctx.org.id, CurriculumCategory.kind == kind)).all())
    cat = CurriculumCategory(org_id=ctx.org.id, kind=kind, title=body.title.strip(), order_index=next_index)
    db.add(cat)
    db.flush()
    audit.log(db, ctx.user, request, "curriculum_category_create", "curriculum_category", cat.id, after={"title": cat.title})
    db.commit()
    return {"id": str(cat.id), "title": cat.title, "order_index": cat.order_index, "items": []}


@router.get("/api/curriculum/categories")
def list_categories(kind: str, ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    """Şablonu (kategori + konu listesi, öğrenci durumu olmadan) yönetmek için — Müfredat sayfası kullanır."""
    kind = _check_kind(kind)
    categories = db.scalars(select(CurriculumCategory).where(
        CurriculumCategory.org_id == ctx.org.id, CurriculumCategory.kind == kind
    ).order_by(CurriculumCategory.order_index)).all()
    out = []
    for cat in categories:
        items = db.scalars(select(CurriculumItem).where(CurriculumItem.category_id == cat.id)
                            .order_by(CurriculumItem.order_index)).all()
        out.append({
            "id": str(cat.id), "title": cat.title, "order_index": cat.order_index,
            "items": [{"id": str(i.id), "title": i.title, "order_index": i.order_index} for i in items],
        })
    return out


@router.delete("/api/curriculum/categories/{category_id}")
def delete_category(category_id: uuid.UUID, request: Request,
                     ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    cat = _get_category(db, ctx, category_id)
    db.delete(cat)
    audit.log(db, ctx.user, request, "curriculum_category_delete", "curriculum_category", cat.id)
    db.commit()
    return {"ok": True}


class CreateItemBody(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@router.post("/api/curriculum/categories/{category_id}/items", status_code=201)
def create_item(category_id: uuid.UUID, body: CreateItemBody, request: Request,
                 ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    cat = _get_category(db, ctx, category_id)
    next_index = len(db.scalars(select(CurriculumItem.id).where(CurriculumItem.category_id == cat.id)).all())
    item = CurriculumItem(category_id=cat.id, title=body.title.strip(), order_index=next_index)
    db.add(item)
    audit.log(db, ctx.user, request, "curriculum_item_create", "curriculum_category", cat.id, after={"title": item.title})
    db.commit()
    return {"id": str(item.id), "title": item.title, "order_index": item.order_index, "status": "-"}


@router.delete("/api/curriculum/items/{item_id}")
def delete_item(item_id: uuid.UUID, request: Request,
                 ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    item = db.get(CurriculumItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item_not_found")
    cat = _get_category(db, ctx, item.category_id)
    db.delete(item)
    audit.log(db, ctx.user, request, "curriculum_item_delete", "curriculum_category", cat.id)
    db.commit()
    return {"ok": True}


class SetStatusBody(BaseModel):
    student_id: uuid.UUID
    status: str


@router.post("/api/curriculum/items/{item_id}/status")
def set_status(item_id: uuid.UUID, body: SetStatusBody, request: Request,
               ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="invalid_status")
    item = db.get(CurriculumItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item_not_found")
    _get_category(db, ctx, item.category_id)  # org sınırı
    if not can_manage_student(db, ctx, body.student_id):
        raise HTTPException(status_code=404, detail="student_not_found")

    row = db.scalar(select(CurriculumStatus).where(
        CurriculumStatus.item_id == item_id, CurriculumStatus.student_id == body.student_id))
    if row:
        row.status = body.status
        row.updated_by = ctx.user.id
    else:
        row = CurriculumStatus(item_id=item_id, student_id=body.student_id, status=body.status, updated_by=ctx.user.id)
        db.add(row)
    audit.log(db, ctx.user, request, "curriculum_status_set", "curriculum_item", item_id,
              after={"student_id": str(body.student_id), "status": body.status})
    db.commit()
    return {"item_id": str(item_id), "student_id": str(body.student_id), "status": row.status}


@router.get("/api/curriculum")
def get_curriculum_for_student(kind: str, student_id: uuid.UUID,
                                ctx: Ctx = Depends(require_perm("tracking.manage")), db: Session = Depends(get_db)):
    kind = _check_kind(kind)
    if not can_manage_student(db, ctx, student_id):
        raise HTTPException(status_code=404, detail="student_not_found")
    return _build_chart(db, ctx.org.id, kind, student_id)


@router.get("/api/me/curriculum")
def get_my_curriculum(kind: str, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    kind = _check_kind(kind)
    return _build_chart(db, ctx.org.id, kind, ctx.user.id)


@router.get("/api/guardians/children/{student_id}/curriculum")
def get_child_curriculum(student_id: uuid.UUID, kind: str, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    kind = _check_kind(kind)
    linked = db.scalar(select(GuardianLink.id).where(
        GuardianLink.student_id == student_id, GuardianLink.guardian_id == ctx.user.id))
    if not linked:
        raise HTTPException(status_code=404, detail="student_not_found")
    return _build_chart(db, ctx.org.id, kind, student_id)
