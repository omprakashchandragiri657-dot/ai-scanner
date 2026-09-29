"""User API endpoints."""

from flask import Blueprint, jsonify, request

from backend.auth import find_by_email
from backend.serializers import user_to_json
from backend.users import fetch_user, fetch_users
from backend.validators import valid_email

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.route("", methods=["GET"])
def list_users():
    return jsonify({"users": fetch_users()})


@bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    record = fetch_user(user_id)
    if record is None:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"user": record})


@bp.route("/lookup", methods=["POST"])
def lookup():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email", "")
    if not valid_email(email):
        return jsonify({"error": "invalid email"}), 400
    row = find_by_email(email)
    if row is None:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"id": row["id"], "email": email})
