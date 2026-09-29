"""Database connection management for FairShare."""

import os
import sqlite3
from contextlib import contextmanager

DATABASE_PATH = os.environ.get("FAIRSHARE_DB", "fairshare.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def transaction():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def table_names():
    cursor = get_connection().cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    )
    return [row["name"] for row in cursor.fetchall()]
