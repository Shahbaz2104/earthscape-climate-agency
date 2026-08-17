from fastapi import APIRouter, Depends, HTTPException
from ..db import q, q1, execute
from ..security import hash_password, verify_password, create_token
from .deps import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["auth"])

DEFAULT_USERS = [
    ("admin", "admin123", "admin"),
    ("analyst", "analyst123", "analyst"),
]


def seed_users():
    for u, p, r in DEFAULT_USERS:
        if not q1("SELECT id FROM users WHERE username=?", (u,)):
            execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)", (u, hash_password(p), r))


@router.post("/login")
def login(body: dict):
    user = q1("SELECT * FROM users WHERE username=?", (body.get("username", ""),))
    if not user or not verify_password(body.get("password", ""), user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    return {"token": create_token(user["id"], user["username"], user["role"]),
            "user": {"id": user["id"], "username": user["username"], "role": user["role"]}}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


@router.get("/users")
def list_users(user=Depends(require_role("admin"))):
    return q("SELECT id, username, role, created_at FROM users")


@router.post("/users")
def create_user(body: dict, user=Depends(require_role("admin"))):
    username = body.get("username", "").strip()
    if not username or len(body.get("password", "")) < 6:
        raise HTTPException(400, "Username required, password min 6 chars")
    if q1("SELECT id FROM users WHERE username=?", (username,)):
        raise HTTPException(409, "Username exists")
    role = body.get("role", "analyst")
    if role not in ("admin", "analyst"):
        raise HTTPException(400, "Role must be admin or analyst")
    execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            (username, hash_password(body["password"]), role))
    return {"ok": True}


@router.patch("/users/{uid}")
def update_user(uid: int, body: dict, user=Depends(require_role("admin"))):
    target = q1("SELECT * FROM users WHERE id=?", (uid,))
    if not target:
        raise HTTPException(404, "User not found")
    if body.get("role") and body["role"] in ("admin", "analyst"):
        execute("UPDATE users SET role=? WHERE id=?", (body["role"], uid))
    if body.get("password"):
        execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(body["password"]), uid))
    return {"ok": True}


@router.delete("/users/{uid}")
def delete_user(uid: int, user=Depends(require_role("admin"))):
    if uid == user["id"]:
        raise HTTPException(400, "Cannot delete yourself")
    execute("DELETE FROM users WHERE id=?", (uid,))
    return {"ok": True}