import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from models.base import IdMixin, TimestampMixin


class CurriculumCategory(IdMixin, Base):
    """Ezber/tecvid çizelgesi başlığı (ör. 'SEVİYE 1', 'Mahreçler'). Kurum başına, tür bazında sıralı."""
    __tablename__ = "curriculum_categories"
    __table_args__ = (UniqueConstraint("org_id", "kind", "order_index"),)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # ezber | tecvid
    title: Mapped[str] = mapped_column(String(160))
    order_index: Mapped[int] = mapped_column(Integer)


class CurriculumItem(IdMixin, Base):
    """Çizelgedeki tek bir konu/dua/sure satırı."""
    __tablename__ = "curriculum_items"
    __table_args__ = (UniqueConstraint("category_id", "order_index"),)

    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_categories.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    order_index: Mapped[int] = mapped_column(Integer)


class CurriculumStatus(IdMixin, TimestampMixin, Base):
    """Bir öğrencinin bir konudaki durumu: '-' | calisiyor | tekrar | ezberlendi."""
    __tablename__ = "curriculum_status"
    __table_args__ = (UniqueConstraint("item_id", "student_id"),)

    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curriculum_items.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="-")
    updated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))


class AttendanceRecord(IdMixin, Base):
    """Bir öğrencinin bir sınıftaki belirli bir tarihteki yoklama durumu."""
    __tablename__ = "attendance_records"
    __table_args__ = (UniqueConstraint("classroom_id", "student_id", "date"),)

    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))  # geldi | gec_geldi | izinli | gelmedi | raporlu
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PageLog(IdMixin, Base):
    """Öğrencinin belirli bir tarihte okuduğu Kur'an sayfa aralığı."""
    __tablename__ = "page_logs"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    log_date: Mapped[date] = mapped_column(Date)
    start_page: Mapped[int] = mapped_column(Integer)
    end_page: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
