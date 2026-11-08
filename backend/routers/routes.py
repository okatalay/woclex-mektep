import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

import audit
from database import get_db
from deps import Ctx, current_ctx, require_perm
from models import Assignment, AssignmentTarget, Enrollment, Route, RouteStop, Submission
from routers.assignments import VALID_TYPES, create_assignment_row
from routers.classes import _get_owned_classroom
from services.classes_targets import resolve_target_student_csv

router = APIRouter(tags=["routes"])


def _route_payload(r: Route, stop_count: int = None) -> dict:
    out = {"id": str(r.id), "classroom_id": str(r.classroom_id), "title": r.title, "description": r.description,
           "created_at": r.created_at.isoformat(),
           "audience": "class" if not r.target_student_ids else "students"}
    if stop_count is not None:
        out["stop_count"] = stop_count
    return out


def _get_route_for_teacher(db: Session, ctx: Ctx, route_id: uuid.UUID) -> Route:
    r = db.get(Route, route_id)
    if not r or r.org_id != ctx.org.id:
        raise HTTPException(status_code=404, detail="route_not_found")
    _get_owned_classroom(db, ctx, r.classroom_id)
    return r


def _ordered_stops(db: Session, route_id: uuid.UUID) -> list[RouteStop]:
    return db.scalars(select(RouteStop).where(RouteStop.route_id == route_id).order_by(RouteStop.order_index)).all()


def _get_stop_for_teacher(db: Session, ctx: Ctx, route_id: uuid.UUID, stop_id: uuid.UUID) -> tuple[Route, RouteStop]:
    r = _get_route_for_teacher(db, ctx, route_id)
    stop = db.get(RouteStop, stop_id)
    if not stop or stop.route_id != r.id:
        raise HTTPException(status_code=404, detail="stop_not_found")
    return r, stop


class CreateRouteBody(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    student_ids: list[uuid.UUID] | None = None


@router.post("/api/classes/{classroom_id}/routes", status_code=201)
def create_route(classroom_id: uuid.UUID, body: CreateRouteBody, request: Request,
                  ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    target_csv = resolve_target_student_csv(db, classroom, body.student_ids)
    r = Route(org_id=ctx.org.id, classroom_id=classroom.id, title=body.title.strip(),
              description=(body.description or "").strip() or None, target_student_ids=target_csv)
    db.add(r)
    db.flush()
    audit.log(db, ctx.user, request, "route_create", "route", r.id, after={"title": r.title})
    db.commit()
    return _route_payload(r, stop_count=0)


@router.get("/api/classes/{classroom_id}/routes")
def list_routes(classroom_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom = _get_owned_classroom(db, ctx, classroom_id)
    rows = db.scalars(select(Route).where(Route.classroom_id == classroom.id).order_by(Route.created_at.desc())).all()
    out = []
    for r in rows:
        stop_count = len(db.scalars(select(RouteStop.id).where(RouteStop.route_id == r.id)).all())
        out.append(_route_payload(r, stop_count))
    return out


@router.get("/api/routes/{route_id}")
def get_route(route_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    r = _get_route_for_teacher(db, ctx, route_id)
    stops = _ordered_stops(db, r.id)
    stop_payloads = []
    for i, stop in enumerate(stops):
        a = db.get(Assignment, stop.assignment_id)
        statuses = db.scalars(select(Submission.status).where(Submission.assignment_id == a.id)).all()
        stop_payloads.append({
            "stop_id": str(stop.id), "order_index": stop.order_index, "assignment_id": str(a.id),
            "title": a.title, "description": a.description, "submission_types": a.submission_types.split(","),
            "target_count": len(statuses),
            "submitted_count": sum(1 for s in statuses if s != "bekliyor"),
            "reviewed_count": sum(1 for s in statuses if s == "incelendi"),
        })
    payload = _route_payload(r, stop_count=len(stops))
    payload["stops"] = stop_payloads
    return payload


class CreateStopBody(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    submission_types: list[str] = Field(default_factory=lambda: ["audio", "text", "file"])


def _route_target_student_ids(r: Route) -> list[uuid.UUID] | None:
    if not r.target_student_ids:
        return None
    return [uuid.UUID(x) for x in r.target_student_ids.split(",") if x]


@router.post("/api/routes/{route_id}/stops", status_code=201)
def create_stop(route_id: uuid.UUID, body: CreateStopBody, request: Request,
                 ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    r = _get_route_for_teacher(db, ctx, route_id)
    classroom = _get_owned_classroom(db, ctx, r.classroom_id)
    a, target_count = create_assignment_row(db, ctx, classroom, body.title, body.description, body.submission_types,
                                             student_ids=_route_target_student_ids(r))

    next_index = len(_ordered_stops(db, r.id))
    stop = RouteStop(route_id=r.id, assignment_id=a.id, order_index=next_index)
    db.add(stop)
    audit.log(db, ctx.user, request, "route_stop_create", "route", r.id, after={"assignment_id": str(a.id)})
    db.commit()
    return {
        "stop_id": str(stop.id), "order_index": stop.order_index, "assignment_id": str(a.id),
        "title": a.title, "description": a.description, "submission_types": a.submission_types.split(","),
        "target_count": target_count, "submitted_count": 0, "reviewed_count": 0,
    }


def _stop_payload(stop: RouteStop, a: Assignment, target_count: int, submitted_count: int, reviewed_count: int) -> dict:
    return {
        "stop_id": str(stop.id), "order_index": stop.order_index, "assignment_id": str(a.id),
        "title": a.title, "description": a.description, "submission_types": a.submission_types.split(","),
        "target_count": target_count, "submitted_count": submitted_count, "reviewed_count": reviewed_count,
    }


class UpdateStopBody(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    submission_types: list[str] | None = None


@router.patch("/api/routes/{route_id}/stops/{stop_id}")
def update_stop(route_id: uuid.UUID, stop_id: uuid.UUID, body: UpdateStopBody, request: Request,
                 ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    r, stop = _get_stop_for_teacher(db, ctx, route_id, stop_id)
    a = db.get(Assignment, stop.assignment_id)
    before = {"title": a.title, "description": a.description, "submission_types": a.submission_types}

    if body.title is not None:
        a.title = body.title.strip()
    if body.description is not None:
        a.description = body.description.strip() or None
    if body.submission_types is not None:
        types = [t for t in body.submission_types if t in VALID_TYPES]
        if not types:
            raise HTTPException(status_code=422, detail="invalid_submission_types")
        a.submission_types = ",".join(types)

    audit.log(db, ctx.user, request, "route_stop_update", "route", r.id, before=before, after={"assignment_id": str(a.id)})
    db.commit()

    statuses = db.scalars(select(Submission.status).where(Submission.assignment_id == a.id)).all()
    return _stop_payload(stop, a, len(statuses), sum(1 for s in statuses if s != "bekliyor"),
                          sum(1 for s in statuses if s == "incelendi"))


@router.delete("/api/routes/{route_id}/stops/{stop_id}", status_code=200)
def delete_stop(route_id: uuid.UUID, stop_id: uuid.UUID, request: Request,
                 ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    r, stop = _get_stop_for_teacher(db, ctx, route_id, stop_id)
    removed_index = stop.order_index
    assignment_id = stop.assignment_id

    db.delete(stop)
    db.flush()
    later_stops = db.scalars(
        select(RouteStop).where(RouteStop.route_id == r.id, RouteStop.order_index > removed_index)
        .order_by(RouteStop.order_index)
    ).all()
    for later in later_stops:
        later.order_index -= 1
        db.flush()  # unique(route_id, order_index) anlık çakışmayı önlemek için tek tek uygula

    a = db.get(Assignment, assignment_id)
    if a:
        db.delete(a)  # ilişkili AssignmentTarget/Submission/SubmissionFile/Review cascade ile silinir

    audit.log(db, ctx.user, request, "route_stop_delete", "route", r.id, before={"assignment_id": str(assignment_id)})
    db.commit()
    return {"ok": True}


class MoveStopBody(BaseModel):
    direction: str = Field(pattern="^(up|down)$")


@router.post("/api/routes/{route_id}/stops/{stop_id}/move")
def move_stop(route_id: uuid.UUID, stop_id: uuid.UUID, body: MoveStopBody, request: Request,
              ctx: Ctx = Depends(require_perm("assignment.manage")), db: Session = Depends(get_db)):
    r, stop = _get_stop_for_teacher(db, ctx, route_id, stop_id)
    neighbor_index = stop.order_index - 1 if body.direction == "up" else stop.order_index + 1
    neighbor = db.scalar(select(RouteStop).where(RouteStop.route_id == r.id, RouteStop.order_index == neighbor_index))
    if not neighbor:
        raise HTTPException(status_code=422, detail="cannot_move")

    # unique(route_id, order_index) anlık çakışmayı önlemek için geçici sentinel ile üç adımda takas
    old_stop_index, old_neighbor_index = stop.order_index, neighbor.order_index
    stop.order_index = -1
    db.flush()
    neighbor.order_index = old_stop_index
    db.flush()
    stop.order_index = old_neighbor_index

    audit.log(db, ctx.user, request, "route_stop_move", "route", r.id, after={"stop_id": str(stop.id), "direction": body.direction})
    db.commit()
    return {"ok": True}


def _student_route_stops(db: Session, route_id: uuid.UUID, student_id: uuid.UUID) -> list[dict]:
    stops = _ordered_stops(db, route_id)
    out = []
    unlocked = True
    for stop in stops:
        a = db.get(Assignment, stop.assignment_id)
        sub = db.scalar(select(Submission).where(Submission.assignment_id == a.id, Submission.student_id == student_id))
        status = sub.status if sub else "bekliyor"
        out.append({
            "stop_id": str(stop.id), "order_index": stop.order_index, "assignment_id": str(a.id),
            "title": a.title, "status": status, "locked": not unlocked,
            "submission_id": str(sub.id) if sub else None,
        })
        unlocked = status == "incelendi"
    return out


@router.get("/api/me/routes")
def my_routes(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    classroom_ids = db.scalars(select(Enrollment.classroom_id).where(
        Enrollment.student_id == ctx.user.id, Enrollment.status == "active")).all()
    if not classroom_ids:
        return []
    routes = db.scalars(select(Route).where(Route.classroom_id.in_(classroom_ids)).order_by(Route.created_at.desc())).all()
    out = []
    for r in routes:
        targets = _route_target_student_ids(r)
        if targets is not None and ctx.user.id not in targets:
            continue
        stops = _student_route_stops(db, r.id, ctx.user.id)
        completed = sum(1 for s in stops if s["status"] == "incelendi")
        out.append({
            **_route_payload(r, stop_count=len(stops)),
            "completed_count": completed,
            "progress_pct": round(completed / len(stops) * 100) if stops else 0,
        })
    return out


@router.get("/api/me/routes/{route_id}")
def my_route_detail(route_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    r = db.get(Route, route_id)
    if not r:
        raise HTTPException(status_code=404, detail="route_not_found")
    enrolled = db.scalar(select(Enrollment.id).where(
        Enrollment.classroom_id == r.classroom_id, Enrollment.student_id == ctx.user.id, Enrollment.status == "active"))
    targets = _route_target_student_ids(r)
    if not enrolled or (targets is not None and ctx.user.id not in targets):
        raise HTTPException(status_code=404, detail="route_not_found")
    stops = _student_route_stops(db, r.id, ctx.user.id)
    completed = sum(1 for s in stops if s["status"] == "incelendi")
    payload = _route_payload(r, stop_count=len(stops))
    payload["stops"] = stops
    payload["completed_count"] = completed
    payload["progress_pct"] = round(completed / len(stops) * 100) if stops else 0
    return payload
