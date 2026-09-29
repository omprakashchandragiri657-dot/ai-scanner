"""JSON serializers for API responses."""

import json

from backend.models import Expense, Group, User


def user_to_json(user: User) -> str:
    return json.dumps(user.to_dict(), separators=(",", ":"))


def expense_to_dict(expense: Expense) -> dict:
    return {
        "id": expense.id,
        "group_id": expense.group_id,
        "paid_by": expense.paid_by,
        "amount_cents": expense.amount_cents,
        "description": expense.description,
        "created_at": expense.created_at,
    }


def group_to_dict(group: Group) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "owner_id": group.owner_id,
        "member_count": len(group.members),
    }


def dumps(payload) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
