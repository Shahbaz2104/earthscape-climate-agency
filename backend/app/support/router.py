from fastapi import APIRouter, Depends, HTTPException
from ..db import q, execute, q1
from ..auth.deps import get_current_user, require_role

router = APIRouter(prefix="/support", tags=["support"])


@router.post("/tickets")
def create_ticket(body: dict, user=Depends(get_current_user)):
    if not body.get("subject", "").strip() or not body.get("body", "").strip():
        raise HTTPException(400, "Subject and body required")
    execute("INSERT INTO tickets (user_id, subject, body) VALUES (?,?,?)",
            (user["id"], body["subject"].strip(), body["body"].strip()))
    return {"ok": True}


@router.get("/tickets")
def list_tickets(user=Depends(get_current_user)):
    if user["role"] == "admin":
        return q("SELECT t.*, u.username FROM tickets t JOIN users u ON u.id=t.user_id ORDER BY t.id DESC")
    return q("SELECT * FROM tickets WHERE user_id=? ORDER BY id DESC", (user["id"],))


@router.patch("/tickets/{tid}")
def update_ticket(tid: int, body: dict, user=Depends(require_role("admin"))):
    t = q1("SELECT * FROM tickets WHERE id=?", (tid,))
    if not t:
        raise HTTPException(404, "Ticket not found")
    if body.get("status") in ("open", "in_progress", "resolved", "closed"):
        execute("UPDATE tickets SET status=? WHERE id=?", (body["status"], tid))
    if body.get("reply"):
        execute("UPDATE tickets SET status='resolved', reply=? WHERE id=?", (body["reply"], tid))
    return {"ok": True}