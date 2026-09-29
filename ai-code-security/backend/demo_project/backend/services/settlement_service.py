"""Settlement calculation service."""

from backend.payments import balances, settle
from backend.services import expense_service


def group_settlement(group_id: int) -> list[dict]:
    rows = expense_service.list_for_group(group_id)
    transactions = []
    for row in rows:
        transactions.append(
            {
                "paid_by": row["paid_by"],
                "amount_cents": row["amount_cents"],
                "participants": [row["paid_by"], row.get("counterparty", row["paid_by"])],
            }
        )
    return settle(balances(transactions))


def summary(group_id: int) -> dict:
    rows = expense_service.list_for_group(group_id)
    total = sum(row["amount_cents"] for row in rows)
    return {"group_id": group_id, "expense_count": len(rows), "total_cents": total}
