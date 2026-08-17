import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["EARTHSCAPE_SECRET"] = "test-secret-0123456789abcdef0123456789abcdef"

import pytest
from app.db import init_db
from app.security import hash_password, verify_password, create_token, decode_token


@pytest.fixture(autouse=True)
def fresh_db():
    init_db()


def test_password_hashing():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_jwt_roundtrip():
    t = create_token(1, "admin", "admin")
    d = decode_token(t)
    assert d["sub"] == "1"
    assert d["role"] == "admin"
    assert decode_token("garbage") is None