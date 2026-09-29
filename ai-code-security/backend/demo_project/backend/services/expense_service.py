"""Expense persistence service."""

from backend.database import get_connection


def list_for_group(group_id: int) -> list[dict]:
    cursor = get_connection().cursor()
    cursor.execute(
        "SELECT id, description, amount_cents, paid_by FROM expenses "
        "WHERE group_id = ? ORDER BY created_at DESC",
        (group_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def create(payload: dict) -> dict:
    cursor = get_connection().cursor()
    cursor.execute(
        "INSERT INTO expenses (group_id, paid_by, amount_cents, description) "
        "VALUES (?, ?, ?, ?)",
        (
            payload["group_id"],
            payload["paid_by"],
            payload["amount_cents"],
            payload["description"],
        ),
    )
    cursor.connection.commit()
    return {
        "id": cursor.lastrowid,
        "group_id": payload["group_id"],
        "amount_cents": payload["amount_cents"],
        "description": payload["description"],
    }


def delete(expense_id: int) -> bool:
    cursor = get_connection().cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    cursor.connection.commit()
    return cursor.rowcount > 0
