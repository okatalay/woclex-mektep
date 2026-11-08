import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.base import IdMixin, TimestampMixin


class Organization(IdMixin, TimestampMixin, Base):
    """Kurum. individual = tek eğitmenin kendi hesabı, institution = çok eğitmenli kurum."""
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(String(16))  # individual | institution
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(32), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(40))
    avatar_url: Mapped[str | None] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    membership: Mapped["Membership | None"] = relationship(back_populates="user", uselist=False)


class Role(IdMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("org_id", "name"),)

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(60))
    system_key: Mapped[str | None] = mapped_column(String(16))  # owner|admin|teacher|student|guardian

    permissions: Mapped[list["RolePermission"]] = relationship(cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission: Mapped[str] = mapped_column(String(40), primary_key=True)


class Membership(IdMixin, TimestampMixin, Base):
    """V1: bir kullanıcı tek organizasyona bağlıdır (user_id unique).

    Bir veli birden çok kurumdaki çocuğa bağlanmak isterse (nadir), bu V1 kapsamı dışıdır.
    """
    __tablename__ = "memberships"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"))

    user: Mapped[User] = relationship(back_populates="membership")
    role: Mapped[Role] = relationship()


class AuditLog(IdMixin, Base):
    __tablename__ = "audit_log"

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(60))
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    before: Mapped[dict | None] = mapped_column(JSONB)
    after: Mapped[dict | None] = mapped_column(JSONB)
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(200))
