"""Organizasyon, sistem rolleri ve kullanıcı oluşturma."""
import re

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Membership, Organization, Role, RolePermission, User
from permissions import SYSTEM_ROLES
from security import hash_password

USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")


def normalize_username(raw: str) -> str:
    u = raw.strip().lower()
    if not USERNAME_RE.match(u):
        raise HTTPException(status_code=422, detail={"username": "invalid_username"})
    return u


def create_org_with_roles(db: Session, name: str, type_: str) -> tuple[Organization, dict[str, Role]]:
    org = Organization(name=name.strip(), type=type_)
    db.add(org)
    db.flush()
    roles: dict[str, Role] = {}
    for key, (label, perms) in SYSTEM_ROLES.items():
        role = Role(org_id=org.id, name=label, system_key=key)
        role.permissions = [RolePermission(permission=p) for p in perms]
        db.add(role)
        roles[key] = role
    db.flush()
    return org, roles


def create_user(
    db: Session, org: Organization, role: Role, username: str, password: str, full_name: str,
    email: str | None = None, phone: str | None = None,
) -> User:
    username = normalize_username(username)
    if db.scalar(select(User.id).where(User.username == username)):
        raise HTTPException(status_code=409, detail={"username": "username_taken"})
    user = User(
        username=username, password_hash=hash_password(password), full_name=full_name.strip(),
        email=(email or None), phone=(phone or None),
    )
    db.add(user)
    db.flush()
    db.add(Membership(user_id=user.id, org_id=org.id, role_id=role.id))
    db.flush()
    return user
