import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import COOKIE_NAME
from database import get_db
from models import Membership, Organization, RolePermission, User
from security import decode_token


@dataclass
class Ctx:
    user: User
    org: Organization
    membership: Membership
    perms: frozenset[str]

    def can(self, perm: str) -> bool:
        return perm in self.perms


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    claims = decode_token(request.cookies.get(COOKIE_NAME, ""))
    user = None
    if claims:
        try:
            user = db.get(User, uuid.UUID(claims["sub"]))
        except (ValueError, KeyError):
            user = None
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="not_authenticated")
    return user


def current_ctx(user: User = Depends(current_user), db: Session = Depends(get_db)) -> Ctx:
    m = user.membership
    if not m:
        raise HTTPException(status_code=403, detail="no_membership")
    org = db.get(Organization, m.org_id)
    if not org or not org.is_active:
        raise HTTPException(status_code=403, detail="org_inactive")
    perms = frozenset(db.scalars(select(RolePermission.permission).where(RolePermission.role_id == m.role_id)))
    return Ctx(user=user, org=org, membership=m, perms=perms)


def require_perm(*codes: str):
    """En az birine sahip olmak yeterli."""
    def dep(ctx: Ctx = Depends(current_ctx)) -> Ctx:
        if not any(ctx.can(c) for c in codes):
            raise HTTPException(status_code=403, detail="forbidden")
        return ctx

    return dep
