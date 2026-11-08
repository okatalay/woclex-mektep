from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from models import AuditLog, User


def log(
    db: Session, user: User | None, request: Request | None, action: str, entity_type: str,
    entity_id=None, before=None, after=None,
) -> None:
    """Denetim kaydı ekler (commit çağıran tarafta: iş ile aynı transaction)."""
    db.add(AuditLog(
        actor_user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        before=jsonable_encoder(before) if before is not None else None,
        after=jsonable_encoder(after) if after is not None else None,
        ip=(request.client.host if request and request.client else None),
        user_agent=(request.headers.get("user-agent", "")[:200] if request else None),
    ))
