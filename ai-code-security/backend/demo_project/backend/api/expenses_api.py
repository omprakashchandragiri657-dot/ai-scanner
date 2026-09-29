"""Expense API endpoints."""

from flask import Blueprint, jsonify, request

from backend.services import expense_service
from backend.validators import validate_expense

bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")


@bp.route("", methods=["GET"])
def list_expenses():
    group_id = request.args.get("group_id", type=int)
    if not group_id:
        return jsonify({"error": "group_id is required"}), 400
    return jsonify({"expenses": expense_service.list_for_group(group_id)})


@bp.route("", methods=["POST"])
def create_expense():
    payload = request.get_json(silent=True) or {}
    errors = validate_expense(payload)
    if errors:
        return jsonify({"errors": errors}), 400
    expense = expense_service.create(payload)
    return jsonify({"expense": expense}), 201


@bp.route("/<int:expense_id>/delete", methods=["POST"])
def delete_expense(expense_id: int):
    removed = expense_service.delete(expense_id)
    if not removed:
        return jsonify({"error": "expense not found"}), 404
    return jsonify({"deleted": expense_id})
