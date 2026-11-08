from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Review, Submission


def student_progress(db: Session, student_id) -> dict:
    """Öğrencinin tüm sınıflardaki ödev/teslim/inceleme özetini türetir."""
    statuses = db.scalars(select(Submission.status).where(Submission.student_id == student_id)).all()
    assigned = len(statuses)
    submitted = sum(1 for s in statuses if s != "bekliyor")
    reviewed = sum(1 for s in statuses if s == "incelendi")
    pending_review = sum(1 for s in statuses if s == "teslim_edildi")
    redo_requested = sum(1 for s in statuses if s == "tekrar_istendi")

    sub_ids = db.scalars(select(Submission.id).where(Submission.student_id == student_id)).all()
    scores = []
    for sid in sub_ids:
        latest = db.scalar(
            select(Review.score).where(Review.submission_id == sid, Review.score.isnot(None))
            .order_by(Review.created_at.desc())
        )
        if latest is not None:
            scores.append(latest)

    return {
        "assigned": assigned,
        "submitted": submitted,
        "reviewed": reviewed,
        "pending_review": pending_review,
        "redo_requested": redo_requested,
        "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
        "completion_rate": round(reviewed / assigned * 100) if assigned else 0,
    }
