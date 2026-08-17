import hashlib, hmac, os, time
import jwt
from .config import JWT_SECRET, JWT_ALGO, JWT_EXPIRE_MINUTES

_ITER = 120_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITER)
    return f"pbkdf2${_ITER}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, dk = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(calc.hex(), dk)
    except Exception:
        return False


def create_token(user_id: int, username: str, role: str) -> str:
    return jwt.encode(
        {"sub": str(user_id), "username": username, "role": role, "exp": int(time.time()) + JWT_EXPIRE_MINUTES * 60},
        JWT_SECRET, algorithm=JWT_ALGO,
    )


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        return None