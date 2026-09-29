"""Group management service."""

from backend.database import get_connection


def create(name: str, owner_id: int) -> dict:
    cursor = get_connection().cursor()
    cursor.execute(
        "INSERT INTO groups (name, owner_id) VALUES (?, ?)",
        (name, owner_id),
    )
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id) VALUES (?, ?)",
        (cursor.lastrowid, owner_id),
    )
    cursor.connection.commit()
    return {"id": cursor.lastrowid, "name": name, "owner_id": owner_id}


def members(group_id: int) -> list[int]:
    cursor = get_connection().cursor()
    cursor.execute(
        "SELECT user_id FROM group_members WHERE group_id = ? ORDER BY user_id",
        (group_id,),
    )
    return [row["user_id"] for row in cursor.fetchall()]


def rename(group_id: int, name: str) -> bool:
    cursor = get_connection().cursor()
    cursor.execute("UPDATE groups SET name = ? WHERE id = ?", (name, group_id))
    cursor.connection.commit()
    return cursor.rowcount > 0
