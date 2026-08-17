from fastapi import Depends, HTTPException, Request
from ..db import q1
from ..security import decode_token


def get_current_user(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    payload = decode_token(auth[7:])
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    user = q1("SELECT * FROM users WHERE id=?", (int(payload["sub"]),))
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user


def require_role(*roles):
    def dep(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(403, f"Requires role: {', '.join(roles)}")
        return user
    return dep