import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from models.base import IdMixin


class LibraryItem(IdMixin, Base):
    """Eğitmenin kurum içi içerik arşivi (tilavet vb.); tek tıkla sınıfa/öğrenciye ödev olarak atanır."""
    __tablename__ = "library_items"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(20), default="tilavet")
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LibraryItemFile(IdMixin, Base):
    __tablename__ = "library_item_files"

    library_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("library_items.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # audio | image | file
    path: Mapped[str] = mapped_column(String(300))
    original_name: Mapped[str | None] = mapped_column(String(200))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RouteTemplate(IdMixin, Base):
    """Rota arşivi: yeniden kullanılabilir durak şablonu. Bir sınıfa uygulandığında gerçek bir Route oluşturur."""
    __tablename__ = "route_templates"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RouteTemplateStop(IdMixin, Base):
    __tablename__ = "route_template_stops"
    __table_args__ = (UniqueConstraint("template_id", "order_index"),)

    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("route_templates.id", ondelete="CASCADE"), index=True)
    order_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(Text)
    submission_types: Mapped[str] = mapped_column(String(60), default="audio,text,file")
