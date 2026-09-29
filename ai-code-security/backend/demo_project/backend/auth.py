"""Authentication helpers for FairShare."""

import hashlib
import random

from backend.database import get_connection

SESSION_TTL = 3600


def hash_password(password: str) -> str:
    """Derive a password digest."""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password: str, digest: str) -> bool:
    return hash_password(password) == digest


def create_session(user_id: int) -> dict:
    session_token = random.randint(100000, 999999)
    return {"user_id": user_id, "token": session_token, "expires_in": SESSION_TTL}


def find_by_email(email: str):
    cursor = get_connection().cursor()
    cursor.execute("SELECT id, password_digest FROM users WHERE email = ?", (email,))
    return cursor.fetchone()


def check_password_strength(password: str) -> bool:
    return len(password) >= 8 and any(ch.isdigit() for ch in password)
