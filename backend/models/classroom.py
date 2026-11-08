import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.base import IdMixin, TimestampMixin


class Classroom(IdMixin, TimestampMixin, Base):
    """Eğitmenin sınıfı. Öğrenciler join_code veya davet linkiyle katılır."""
    __tablename__ = "classrooms"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    join_code: Mapped[str] = mapped_column(String(24), unique=True)
    join_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)


class Enrollment(IdMixin, Base):
    """Öğrencinin bir sınıfa kaydı."""
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("classroom_id", "student_id"),)

    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active | removed
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GuardianLink(IdMixin, Base):
    """Veli-öğrenci bağı. Bir veli birden çok çocuğa, bir çocuk birden çok veliye bağlanabilir."""
    __tablename__ = "guardian_links"
    __table_args__ = (UniqueConstraint("student_id", "guardian_id"),)

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    relation: Mapped[str | None] = mapped_column(String(40))  # anne | baba | veli | ...
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GuardianInvite(IdMixin, Base):
    """Öğrenci kartından üretilen tek kullanımlık veli davet linki."""
    __tablename__ = "guardian_invites"

    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    relation_hint: Mapped[str | None] = mapped_column(String(40))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
