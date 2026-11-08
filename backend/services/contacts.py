from sqlalchemy import select
from sqlalchemy.orm import Session

from deps import Ctx
from models import Classroom, Enrollment, GuardianLink, User


def eligible_contacts(db: Session, ctx: Ctx) -> list[dict]:
    """ctx.user'ın mesajlaşabileceği kişiler: eğitmen<->öğrenci, eğitmen<->veli (aynı kurum, aktif kayıt üzerinden)."""
    role = ctx.membership.role.system_key

    if role in ("owner", "admin", "teacher"):
        classroom_q = select(Classroom.id).where(Classroom.org_id == ctx.org.id, Classroom.is_archived.is_(False))
        if not ctx.can("classroom.manage_all"):
            classroom_q = classroom_q.where(Classroom.teacher_id == ctx.user.id)
        classroom_ids = db.scalars(classroom_q).all()
        if not classroom_ids:
            return []

        students = db.execute(
            select(User, Enrollment.classroom_id)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(Enrollment.classroom_id.in_(classroom_ids), Enrollment.status == "active")
        ).all()
        student_ids = [u.id for u, _ in students]
        classroom_names = {c.id: c.name for c in db.scalars(select(Classroom).where(Classroom.id.in_(classroom_ids)))}

        out = [
            {"user_id": str(u.id), "full_name": u.full_name, "role": "student", "context": classroom_names.get(cid, "")}
            for u, cid in students
        ]
        if student_ids:
            guardians = db.execute(
                select(User, GuardianLink.student_id)
                .join(GuardianLink, GuardianLink.guardian_id == User.id)
                .where(GuardianLink.student_id.in_(student_ids))
            ).all()
            student_names = {u.id: u.full_name for u, _ in students}
            out += [
                {"user_id": str(u.id), "full_name": u.full_name, "role": "guardian",
                 "context": f"{student_names.get(sid, '')} velisi"}
                for u, sid in guardians
            ]
        return out

    if role == "student":
        rows = db.execute(
            select(User, Classroom.name)
            .join(Classroom, Classroom.teacher_id == User.id)
            .join(Enrollment, Enrollment.classroom_id == Classroom.id)
            .where(Enrollment.student_id == ctx.user.id, Enrollment.status == "active")
        ).all()
        return [{"user_id": str(u.id), "full_name": u.full_name, "role": "teacher", "context": name} for u, name in rows]

    if role == "guardian":
        rows = db.execute(
            select(User, Classroom.name)
            .join(Classroom, Classroom.teacher_id == User.id)
            .join(Enrollment, Enrollment.classroom_id == Classroom.id)
            .join(GuardianLink, GuardianLink.student_id == Enrollment.student_id)
            .where(GuardianLink.guardian_id == ctx.user.id, Enrollment.status == "active")
        ).all()
        seen = {}
        for u, name in rows:
            seen.setdefault(u.id, {"user_id": str(u.id), "full_name": u.full_name, "role": "teacher", "context": name})
        return list(seen.values())

    return []


def is_eligible_contact(db: Session, ctx: Ctx, peer_id) -> bool:
    return str(peer_id) in {c["user_id"] for c in eligible_contacts(db, ctx)}
