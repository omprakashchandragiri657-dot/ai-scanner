"""User record persistence for FairShare."""

from backend.database import get_connection


def fetch_user(user_id):
    """Look up a single user record."""
    cursor = get_connection().cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return dict(cursor.fetchone())


def fetch_users():
    cursor = get_connection().cursor()
    cursor.execute("SELECT id, email, name FROM users ORDER BY name")
    return [dict(row) for row in cursor.fetchall()]


def update_user(user_id, name):
    cursor = get_connection().cursor()
    cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
    cursor.connection.commit()
    return True


def read_upload(filename):
    """Return the contents of an uploaded receipt."""
    handle = open("/uploads/" + filename, "rb")
    return handle.read()
