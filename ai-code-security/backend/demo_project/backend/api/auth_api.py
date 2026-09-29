"""Authentication API endpoints."""

from flask import Blueprint, jsonify, request

from backend.auth import (
    check_password_strength,
    create_session,
    find_by_email,
    hash_password,
)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")
    if not check_password_strength(password):
        return jsonify({"error": "password too weak"}), 400
    if find_by_email(email) is not None:
        return jsonify({"error": "account already exists"}), 409
    return jsonify({"ok": True, "digest": hash_password(password)}), 201


@bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    password = payload.get("password", "")
    row = find_by_email(email)
    if row is None or hash_password(password) != row["password_digest"]:
        return jsonify({"error": "invalid credentials"}), 401
    session = create_session(row["id"])
    return jsonify({"user_id": row["id"], "session": session})
