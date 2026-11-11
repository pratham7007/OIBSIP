"""Parameterized-query examples for code review; no exploit inputs are included."""

import sqlite3
from contextlib import closing


def find_account(database_path: str, account_id: int) -> tuple | None:
    if account_id <= 0:
        raise ValueError("account_id must be a positive integer")
    with closing(sqlite3.connect(database_path)) as connection:
        return connection.execute(
            "SELECT id, display_name FROM accounts WHERE id = ?",
            (account_id,),
        ).fetchone()


def find_account_by_name(database_path: str, display_name: str) -> list[tuple]:
    if not display_name or len(display_name) > 100:
        raise ValueError("display_name must be between 1 and 100 characters")
    with closing(sqlite3.connect(database_path)) as connection:
        return connection.execute(
            "SELECT id, display_name FROM accounts WHERE display_name = ?",
            (display_name,),
        ).fetchall()
