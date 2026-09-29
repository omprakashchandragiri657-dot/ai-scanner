"""Health check endpoints."""

from flask import Blueprint

from backend.serializers import dumps

bp = Blueprint("health", __name__, url_prefix="/api/health")


@bp.route("", methods=["GET"])
def health():
    return dumps({"status": "ok", "service": "fairshare"}), 200, {
        "Content-Type": "application/json"
    }
