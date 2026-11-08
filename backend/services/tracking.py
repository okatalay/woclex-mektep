"""Yoklama, ezber/tecvid çizelgesi ve sayfa takibinin ortak özet hesapları."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import AttendanceRecord, CurriculumCategory, CurriculumItem, CurriculumStatus, PageLog

ATTENDANCE_PRESENT = {"geldi", "gec_geldi"}


def curriculum_completion(db: Session, org_id, kind: str, student_id) -> dict:
    item_ids = db.scalars(
        select(CurriculumItem.id)
        .join(CurriculumCategory, CurriculumCategory.id == CurriculumItem.category_id)
        .where(CurriculumCategory.org_id == org_id, CurriculumCategory.kind == kind)
    ).all()
    total = len(item_ids)
    if not total:
        return {"completed": 0, "total": 0, "pct": 0}
    completed = db.scalar(
        select(func.count(CurriculumStatus.id)).where(
            CurriculumStatus.item_id.in_(item_ids), CurriculumStatus.student_id == student_id,
            CurriculumStatus.status == "ezberlendi",
        )
    ) or 0
    return {"completed": completed, "total": total, "pct": round(completed / total * 100)}


def page_summary(db: Session, student_id) -> dict:
    rows = db.scalars(select(PageLog).where(PageLog.student_id == student_id).order_by(PageLog.log_date.desc())).all()
    total_read = sum(max(r.end_page - r.start_page + 1, 0) for r in rows)
    return {"current_page": rows[0].end_page if rows else None, "total_read": total_read, "log_count": len(rows)}


def attendance_summary(db: Session, student_id) -> dict:
    statuses = db.scalars(select(AttendanceRecord.status).where(AttendanceRecord.student_id == student_id)).all()
    total = len(statuses)
    present = sum(1 for s in statuses if s in ATTENDANCE_PRESENT)
    return {"total": total, "present": present, "rate_pct": round(present / total * 100) if total else 0}


def badge_for_pct(pct: float) -> str | None:
    if pct >= 100:
        return "Altın Rozet"
    if pct >= 50:
        return "Gümüş Rozet"
    if pct > 0:
        return "Başlangıç Rozeti"
    return None


def student_tracking_summary(db: Session, org_id, student_id) -> dict:
    ezber = curriculum_completion(db, org_id, "ezber", student_id)
    tecvid = curriculum_completion(db, org_id, "tecvid", student_id)
    total_items = ezber["total"] + tecvid["total"]
    total_completed = ezber["completed"] + tecvid["completed"]
    overall_pct = round(total_completed / total_items * 100) if total_items else 0
    return {
        "ezber": ezber,
        "tecvid": tecvid,
        "pages": page_summary(db, student_id),
        "attendance": attendance_summary(db, student_id),
        "overall_pct": overall_pct,
        "badge": badge_for_pct(overall_pct),
    }
