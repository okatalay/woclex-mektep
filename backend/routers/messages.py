import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

import audit
from database import get_db
from deps import Ctx, current_ctx
from models import Conversation, ConversationMember, Message, User
from services.contacts import eligible_contacts, is_eligible_contact

router = APIRouter(prefix="/api/messages", tags=["messages"])

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _get_membership(db: Session, ctx: Ctx, conversation_id: uuid.UUID) -> ConversationMember:
    m = db.scalar(select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id, ConversationMember.user_id == ctx.user.id))
    if not m:
        raise HTTPException(status_code=404, detail="conversation_not_found")
    return m


@router.get("/contacts")
def list_contacts(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    return eligible_contacts(db, ctx)


@router.get("/conversations")
def list_conversations(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    my_memberships = db.scalars(select(ConversationMember).where(ConversationMember.user_id == ctx.user.id)).all()
    out = []
    for mine in my_memberships:
        peer_m = db.scalar(select(ConversationMember).where(
            ConversationMember.conversation_id == mine.conversation_id, ConversationMember.user_id != ctx.user.id))
        peer = peer_m and db.get(User, peer_m.user_id)
        if not peer:
            continue
        last_msg = db.scalar(
            select(Message).where(Message.conversation_id == mine.conversation_id)
            .order_by(Message.created_at.desc()).limit(1)
        )
        unread = db.scalar(
            select(func.count(Message.id)).where(
                Message.conversation_id == mine.conversation_id,
                Message.sender_id != ctx.user.id,
                Message.created_at > (mine.last_read_at or EPOCH),
            )
        )
        out.append({
            "conversation_id": str(mine.conversation_id),
            "peer": {"user_id": str(peer.id), "full_name": peer.full_name},
            "last_message": last_msg.body if last_msg else None,
            "last_message_at": last_msg.created_at.isoformat() if last_msg else None,
            "unread_count": unread or 0,
        })
    out.sort(key=lambda c: c["last_message_at"] or "", reverse=True)
    return out


@router.get("/unread-count")
def unread_count(ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    memberships = db.scalars(select(ConversationMember).where(ConversationMember.user_id == ctx.user.id)).all()
    total = 0
    for m in memberships:
        total += db.scalar(
            select(func.count(Message.id)).where(
                Message.conversation_id == m.conversation_id,
                Message.sender_id != ctx.user.id,
                Message.created_at > (m.last_read_at or EPOCH),
            )
        ) or 0
    return {"unread_count": total}


class StartConversationBody(BaseModel):
    peer_user_id: uuid.UUID


@router.post("/conversations", status_code=201)
def start_conversation(body: StartConversationBody, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    if body.peer_user_id == ctx.user.id:
        raise HTTPException(status_code=422, detail="invalid_peer")
    if not is_eligible_contact(db, ctx, body.peer_user_id):
        raise HTTPException(status_code=404, detail="contact_not_found")

    a, b = aliased(ConversationMember), aliased(ConversationMember)
    existing = db.scalar(
        select(a.conversation_id).join(b, a.conversation_id == b.conversation_id)
        .where(a.user_id == ctx.user.id, b.user_id == body.peer_user_id)
    )
    if existing:
        return {"conversation_id": str(existing)}

    conv = Conversation(org_id=ctx.org.id)
    db.add(conv)
    db.flush()
    db.add(ConversationMember(conversation_id=conv.id, user_id=ctx.user.id))
    db.add(ConversationMember(conversation_id=conv.id, user_id=body.peer_user_id))
    db.commit()
    return {"conversation_id": str(conv.id)}


@router.get("/conversations/{conversation_id}/messages")
def list_messages(conversation_id: uuid.UUID, ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    membership = _get_membership(db, ctx, conversation_id)
    rows = db.scalars(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
    ).all()
    membership.last_read_at = datetime.now(timezone.utc)
    db.commit()
    return [
        {"id": str(m.id), "sender_id": str(m.sender_id), "body": m.body, "created_at": m.created_at.isoformat(),
         "mine": m.sender_id == ctx.user.id}
        for m in rows
    ]


class SendMessageBody(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


@router.post("/conversations/{conversation_id}/messages", status_code=201)
def send_message(conversation_id: uuid.UUID, body: SendMessageBody, request: Request,
                  ctx: Ctx = Depends(current_ctx), db: Session = Depends(get_db)):
    membership = _get_membership(db, ctx, conversation_id)
    msg = Message(conversation_id=conversation_id, sender_id=ctx.user.id, body=body.body.strip())
    db.add(msg)
    membership.last_read_at = datetime.now(timezone.utc)
    audit.log(db, ctx.user, request, "message_send", "conversation", conversation_id)
    db.commit()
    return {"id": str(msg.id), "sender_id": str(ctx.user.id), "body": msg.body, "created_at": msg.created_at.isoformat(), "mine": True}
