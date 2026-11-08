"""Nesne erişim kuralları. Router'lar sahiplik/rol kontrolünü elle yazmaz, buradan sorar.

Erişimi olmayan kayıt için 404 (varlığı sızdırma), yetkisiz eylem için 403 döndürülür.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from deps import Ctx
from models import Classroom, Enrollment, GuardianLink


def can_manage_classroom(ctx: Ctx, classroom: Classroom) -> bool:
    """Sınıfın sahibi eğitmen, ya da kurumun tüm sınıflarını yönetme izni olan (owner/admin)."""
    if classroom.org_id != ctx.org.id:
        return False
    if ctx.can("classroom.manage_all"):
        return True
    return classroom.teacher_id == ctx.user.id and ctx.can("classroom.manage_own")


def can_view_classroom(ctx: Ctx, classroom: Classroom) -> bool:
    if classroom.org_id != ctx.org.id:
        return False
    return can_manage_classroom(ctx, classroom)


def is_student_of(db: Session, ctx: Ctx, student_id) -> bool:
    """ctx.user öğrencinin kendisi mi."""
    return ctx.user.id == student_id


def is_guardian_of(db: Session, ctx: Ctx, student_id) -> bool:
    return db.scalar(
        select(GuardianLink.id).where(GuardianLink.student_id == student_id, GuardianLink.guardian_id == ctx.user.id)
    ) is not None


def can_manage_student(db: Session, ctx: Ctx, student_id) -> bool:
    """Öğrenci, ctx.user'ın yönetebildiği en az bir sınıfa aktif kayıtlı mı (org sınırı dahil)."""
    rows = db.execute(
        select(Enrollment.classroom_id, Classroom)
        .join(Classroom, Classroom.id == Enrollment.classroom_id)
        .where(Enrollment.student_id == student_id, Enrollment.status == "active")
    ).all()
    return any(can_manage_classroom(ctx, classroom) for _, classroom in rows)


def is_enrolled(db: Session, classroom_id, student_id) -> bool:
    return db.scalar(
        select(Enrollment.id).where(
            Enrollment.classroom_id == classroom_id, Enrollment.student_id == student_id,
            Enrollment.status == "active",
        )
    ) is not None
