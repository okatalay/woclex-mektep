import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from models.base import IdMixin, TimestampMixin


class Assignment(IdMixin, TimestampMixin, Base):
    """Eğitmenin bir sınıfa atadığı ödev."""
    __tablename__ = "assignments"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    submission_types: Mapped[str] = mapped_column(String(60), default="audio,text,file")  # csv
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AssignmentTarget(IdMixin, Base):
    """Ödevin atandığı öğrenci (oluşturma anında sınıftaki aktif öğrenciler eklenir)."""
    __tablename__ = "assignment_targets"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id"),)

    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)


class Submission(IdMixin, TimestampMixin, Base):
    """Öğrencinin bir ödeve teslimi. bekliyor -> teslim_edildi -> incelendi | tekrar_istendi."""
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id"),)

    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="bekliyor")
    text_content: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubmissionFile(IdMixin, Base):
    __tablename__ = "submission_files"

    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # audio | image | file
    path: Mapped[str] = mapped_column(String(300))
    original_name: Mapped[str | None] = mapped_column(String(200))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AssignmentAttachment(IdMixin, Base):
    """Öğretmenin ödeve eklediği materyal (ses/görsel/dosya)."""
    __tablename__ = "assignment_attachments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # audio | image | file
    path: Mapped[str] = mapped_column(String(300))
    original_name: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Review(IdMixin, Base):
    """Eğitmenin bir teslime verdiği puan/geri bildirim."""
    __tablename__ = "reviews"

    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    score: Mapped[int | None] = mapped_column(Integer)  # 1-5
    feedback_text: Mapped[str | None] = mapped_column(Text)
    request_redo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
