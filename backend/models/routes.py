import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from models.base import IdMixin


class Route(IdMixin, Base):
    """Eğitmenin sınıf için tanımladığı adım adım öğrenme rotası (yolculuk haritası)."""
    __tablename__ = "routes"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    classroom_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classrooms.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    target_student_ids: Mapped[str | None] = mapped_column(Text)  # csv; boş -> tüm sınıf
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RouteStop(IdMixin, Base):
    """Rotadaki bir durak; her durak bir ödeve (Assignment) karşılık gelir.

    Bir sonraki durak, öğrencinin önceki durağı 'incelendi' durumuna getirmesiyle açılır.
    """
    __tablename__ = "route_stops"
    __table_args__ = (UniqueConstraint("route_id", "order_index"), UniqueConstraint("assignment_id"))

    route_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), index=True)
    assignment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"))
    order_index: Mapped[int] = mapped_column(Integer)
