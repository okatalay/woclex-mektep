import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Enrollment


def resolve_target_student_csv(db: Session, classroom, student_ids: list[uuid.UUID] | None) -> str | None:
    """`student_ids` None ise tüm sınıf (None döner); verilmişse sınıftaki aktif öğrencilerle kesişimin
    CSV'sini döner. Kesişim boşsa 422 fırlatır."""
    if student_ids is None:
        return None
    active_students = set(db.scalars(select(Enrollment.student_id).where(
        Enrollment.classroom_id == classroom.id, Enrollment.status == "active")).all())
    chosen = active_students & set(student_ids)
    if not chosen:
        raise HTTPException(status_code=422, detail="no_valid_students")
    return ",".join(str(x) for x in chosen)
