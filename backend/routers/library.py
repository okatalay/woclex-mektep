import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import (
    AssignmentAttachment, LibraryItem, LibraryItemFile, Route, RouteStop, RouteTemplate, RouteTemplateStop,
)
from routers.assignments import VALID_TYPES, create_assignment_row
from routers.classes import _get_owned_classroom
from routers.routes import _route_target_student_ids
from services.classes_targets import resolve_target_student_csv
from services.storage import copy_file, delete_file, resolve_path, save_file

router = APIRouter(tags=["library"])


# ---------- Tilavet arşivi (içerik kütüphanesi) ----------

def _library_file_payload(f: LibraryItemFile) -> dict:
    return {"id": str(f.id), "kind": f.kind, "original_name": f.original_name, "note": f.note,
            "url": f"/api/library/files/{f.id}"}


def _library_item_payload(item: LibraryItem, files: list[LibraryItemFile] = None) -> dict:
    out = {"id": str(item.id), "kind": item.kind, "title": item.title, "description": item.description,
           "created_at": item.created_at.isoformat()}
    if files is not None:
        out["files"] = [_library_file_payload(f) for f in files]
    return out


def _get_library_item(db: Session, ctx: Ctx, item_id: uuid.UUID) -> LibraryItem:
    item = db.get(LibraryItem, item_id)
    if not item or item.org_id != ctx.org.id:
        raise HTTPException(status_code=404, detail="library_item_not_found")
    return item


class CreateLibraryItemBody(BaseModel):
    kind: str = Field(default="tilavet", max_length=20)
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)


@router.post("/api/library", status_code=201)
def create_library_item(body: CreateLibraryItemBody, request: Request,
                         ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    item = LibraryItem(org_id=ctx.org.id, created_by=ctx.user.id, kind=body.kind.strip() or "tilavet",
                        title=body.title.strip(), description=(body.description or "").strip() or None)
    db.add(item)
    db.flush()
    audit.log(db, ctx.user, request, "library_item_create", "library_item", item.id, after={"title": item.title})
    db.commit()
    return _library_item_payload(item, files=[])


@router.get("/api/library")
def list_library_items(kind: str | None = None, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    q = select(LibraryItem).where(LibraryItem.org_id == ctx.org.id)
    if kind:
        q = q.where(LibraryItem.kind == kind)
    rows = db.scalars(q.order_by(LibraryItem.created_at.desc())).all()
    return [_library_item_payload(i) for i in rows]


@router.get("/api/library/{item_id}")
def get_library_item(item_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    item = _get_library_item(db, ctx, item_id)
    files = db.scalars(select(LibraryItemFile).where(LibraryItemFile.library_item_id == item.id)
                        .order_by(LibraryItemFile.created_at)).all()
    return _library_item_payload(item, files=files)


@router.delete("/api/library/{item_id}")
def delete_library_item(item_id: uuid.UUID, request: Request,
                         ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    item = _get_library_item(db, ctx, item_id)
    files = db.scalars(select(LibraryItemFile).where(LibraryItemFile.library_item_id == item.id)).all()
    for f in files:
        delete_file(f.path)
    db.delete(item)
    audit.log(db, ctx.user, request, "library_item_delete", "library_item", item.id)
    db.commit()
    return {"ok": True}


@router.post("/api/library/{item_id}/files", status_code=201)
def add_library_files(item_id: uuid.UUID, request: Request, files: list[UploadFile] = File(...),
                       note: str | None = None,
                       ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    item = _get_library_item(db, ctx, item_id)
    added = []
    for f in files:
        if not f.filename:
            continue
        rel, kind = save_file("library", item.id, f)
        row = LibraryItemFile(library_item_id=item.id, kind=kind, path=rel, original_name=f.filename, note=note)
        db.add(row)
        added.append(row)
    audit.log(db, ctx.user, request, "library_item_files_add", "library_item", item.id, after={"count": len(added)})
    db.commit()
    return [_library_file_payload(f) for f in added]


class FromArchiveBody(BaseModel):
    item_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


def _archive_files(db: Session, ctx: Ctx, item_ids: list[uuid.UUID]) -> list[LibraryItemFile]:
    files: list[LibraryItemFile] = []
    for iid in item_ids:
        item = _get_library_item(db, ctx, iid)
        files += db.scalars(select(LibraryItemFile).where(LibraryItemFile.library_item_id == item.id)
                             .order_by(LibraryItemFile.created_at)).all()
    return files


@router.post("/api/library/{item_id}/files/from-archive", status_code=201)
def add_library_files_from_archive(item_id: uuid.UUID, body: FromArchiveBody, request: Request,
                                    ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    """Arşiv içeriklerinin dosyalarını bu maddeye kopyalar."""
    item = _get_library_item(db, ctx, item_id)
    added = []
    for f in _archive_files(db, ctx, body.item_ids):
        row = LibraryItemFile(library_item_id=item.id, kind=f.kind, original_name=f.original_name, note=f.note,
                               path=copy_file(f.path, "library", item.id))
        db.add(row)
        added.append(row)
    audit.log(db, ctx.user, request, "library_item_files_from_archive", "library_item", item.id,
              after={"count": len(added)})
    db.commit()
    return [_library_file_payload(f) for f in added]


@router.delete("/api/library/{item_id}/files/{file_id}")
def delete_library_file(item_id: uuid.UUID, file_id: uuid.UUID, request: Request,
                         ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    item = _get_library_item(db, ctx, item_id)
    f = db.get(LibraryItemFile, file_id)
    if not f or f.library_item_id != item.id:
        raise HTTPException(status_code=404, detail="file_not_found")
    delete_file(f.path)
    db.delete(f)
    audit.log(db, ctx.user, request, "library_item_file_delete", "library_item", item.id)
    db.commit()
    return {"ok": True}


@router.get("/api/library/files/{file_id}")
def get_library_file(file_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    f = db.get(LibraryItemFile, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="not_found")
    item = db.get(LibraryItem, f.library_item_id)
    if not item or item.org_id != ctx.org.id:
        raise HTTPException(status_code=404, detail="not_found")
    path = resolve_path(f.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="not_found")
    return FileResponse(path, filename=f.original_name or path.name)


class AssignLibraryItemBody(BaseModel):
    classroom_id: uuid.UUID
    student_ids: list[uuid.UUID] | None = None
    due_at: datetime | None = None
    submission_types: list[str] | None = None


@router.post("/api/library/{item_id}/assign", status_code=201)
def assign_library_item(item_id: uuid.UUID, body: AssignLibraryItemBody, request: Request,
                         ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    """Arşiv maddesini ödev olarak oluşturur ve maddedeki dosyaları ödev materyaline kopyalar."""
    item = _get_library_item(db, ctx, item_id)
    classroom = _get_owned_classroom(db, ctx, body.classroom_id)
    types = [t for t in (body.submission_types or ["audio", "text"]) if t in VALID_TYPES] or ["audio", "text"]
    a, target_count = create_assignment_row(
        db, ctx, classroom, item.title, item.description, types, body.due_at, body.student_ids,
    )
    files = db.scalars(select(LibraryItemFile).where(LibraryItemFile.library_item_id == item.id)).all()
    for f in files:
        db.add(AssignmentAttachment(assignment_id=a.id, kind=f.kind, original_name=f.original_name,
                                    path=copy_file(f.path, "assignment-materials", a.id)))
    audit.log(db, ctx.user, request, "library_item_assign", "library_item", item.id,
              after={"assignment_id": str(a.id)})
    db.commit()
    return {"assignment_id": str(a.id), "classroom_id": str(classroom.id), "target_count": target_count}


# ---------- Rota arşivi (yeniden kullanılabilir yolculuk şablonları) ----------

def _template_payload(t: RouteTemplate, stop_count: int = None) -> dict:
    out = {"id": str(t.id), "title": t.title, "description": t.description, "created_at": t.created_at.isoformat()}
    if stop_count is not None:
        out["stop_count"] = stop_count
    return out


def _template_stop_payload(s: RouteTemplateStop) -> dict:
    return {"id": str(s.id), "order_index": s.order_index, "title": s.title, "description": s.description,
            "submission_types": s.submission_types.split(",")}


def _get_route_template(db: Session, ctx: Ctx, template_id: uuid.UUID) -> RouteTemplate:
    t = db.get(RouteTemplate, template_id)
    if not t or t.org_id != ctx.org.id:
        raise HTTPException(status_code=404, detail="route_template_not_found")
    return t


class CreateRouteTemplateBody(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


@router.post("/api/route-templates", status_code=201)
def create_route_template(body: CreateRouteTemplateBody, request: Request,
                           ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    t = RouteTemplate(org_id=ctx.org.id, created_by=ctx.user.id, title=body.title.strip(),
                       description=(body.description or "").strip() or None)
    db.add(t)
    db.flush()
    audit.log(db, ctx.user, request, "route_template_create", "route_template", t.id, after={"title": t.title})
    db.commit()
    return _template_payload(t, stop_count=0)


@router.get("/api/route-templates")
def list_route_templates(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    rows = db.scalars(select(RouteTemplate).where(RouteTemplate.org_id == ctx.org.id)
                       .order_by(RouteTemplate.created_at.desc())).all()
    out = []
    for t in rows:
        stop_count = len(db.scalars(select(RouteTemplateStop.id).where(RouteTemplateStop.template_id == t.id)).all())
        out.append(_template_payload(t, stop_count))
    return out


@router.get("/api/route-templates/{template_id}")
def get_route_template(template_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    t = _get_route_template(db, ctx, template_id)
    stops = db.scalars(select(RouteTemplateStop).where(RouteTemplateStop.template_id == t.id)
                        .order_by(RouteTemplateStop.order_index)).all()
    payload = _template_payload(t, stop_count=len(stops))
    payload["stops"] = [_template_stop_payload(s) for s in stops]
    return payload


@router.delete("/api/route-templates/{template_id}")
def delete_route_template(template_id: uuid.UUID, request: Request,
                           ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    t = _get_route_template(db, ctx, template_id)
    db.delete(t)
    audit.log(db, ctx.user, request, "route_template_delete", "route_template", t.id)
    db.commit()
    return {"ok": True}


class CreateTemplateStopBody(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    submission_types: list[str] = Field(default_factory=lambda: ["audio", "text", "file"])


@router.post("/api/route-templates/{template_id}/stops", status_code=201)
def add_template_stop(template_id: uuid.UUID, body: CreateTemplateStopBody, request: Request,
                       ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    t = _get_route_template(db, ctx, template_id)
    types = [x for x in body.submission_types if x in VALID_TYPES]
    if not types:
        raise HTTPException(status_code=422, detail="invalid_submission_types")
    next_index = len(db.scalars(select(RouteTemplateStop.id).where(RouteTemplateStop.template_id == t.id)).all())
    stop = RouteTemplateStop(template_id=t.id, order_index=next_index, title=body.title.strip(),
                              description=(body.description or "").strip() or None, submission_types=",".join(types))
    db.add(stop)
    audit.log(db, ctx.user, request, "route_template_stop_add", "route_template", t.id, after={"title": stop.title})
    db.commit()
    return _template_stop_payload(stop)


@router.delete("/api/route-templates/{template_id}/stops/{stop_id}")
def delete_template_stop(template_id: uuid.UUID, stop_id: uuid.UUID, request: Request,
                          ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    t = _get_route_template(db, ctx, template_id)
    stop = db.get(RouteTemplateStop, stop_id)
    if not stop or stop.template_id != t.id:
        raise HTTPException(status_code=404, detail="stop_not_found")
    removed_index = stop.order_index
    db.delete(stop)
    db.flush()
    later = db.scalars(select(RouteTemplateStop).where(
        RouteTemplateStop.template_id == t.id, RouteTemplateStop.order_index > removed_index,
    ).order_by(RouteTemplateStop.order_index)).all()
    for later_stop in later:
        later_stop.order_index -= 1
        db.flush()
    audit.log(db, ctx.user, request, "route_template_stop_delete", "route_template", t.id)
    db.commit()
    return {"ok": True}


class ApplyTemplateBody(BaseModel):
    classroom_id: uuid.UUID
    student_ids: list[uuid.UUID] | None = None
    title: str | None = Field(default=None, max_length=160)


@router.post("/api/route-templates/{template_id}/apply", status_code=201)
def apply_route_template(template_id: uuid.UUID, body: ApplyTemplateBody, request: Request,
                          ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    """Şablonu bir sınıfa (veya seçili öğrencilere) uygular: gerçek bir Route + durakları oluşturur."""
    t = _get_route_template(db, ctx, template_id)
    classroom = _get_owned_classroom(db, ctx, body.classroom_id)
    stops = db.scalars(select(RouteTemplateStop).where(RouteTemplateStop.template_id == t.id)
                        .order_by(RouteTemplateStop.order_index)).all()
    if not stops:
        raise HTTPException(status_code=422, detail="template_has_no_stops")

    target_csv = resolve_target_student_csv(db, classroom, body.student_ids)

    route = Route(org_id=ctx.org.id, classroom_id=classroom.id, title=(body.title or t.title).strip(),
                  description=t.description, target_student_ids=target_csv)
    db.add(route)
    db.flush()

    student_ids = _route_target_student_ids(route)
    for i, tstop in enumerate(stops):
        a, _ = create_assignment_row(db, ctx, classroom, tstop.title, tstop.description,
                                      tstop.submission_types.split(","), student_ids=student_ids)
        db.add(RouteStop(route_id=route.id, assignment_id=a.id, order_index=i))

    audit.log(db, ctx.user, request, "route_template_apply", "route_template", t.id,
              after={"route_id": str(route.id)})
    db.commit()
    return {"route_id": str(route.id), "stop_count": len(stops)}
