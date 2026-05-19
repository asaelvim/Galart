import os
import sys
import sqlite3

from db.init_db import init_db


def _get_db_path() -> str:
    """Return the path to galart.db, works in dev and inside a PyInstaller bundle."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller executable — place .db next to the .exe
        base = os.path.dirname(sys.executable)
    else:
        # Running from source — place .db at the project root
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "galart.db")


class _Row:
    """Row wrapper that supports both index-based and attribute-based access."""

    __slots__ = ("_data", "_fields")

    def __init__(self, cursor, row):
        object.__setattr__(self, "_data", row)
        fields = [d[0] for d in cursor.description]
        object.__setattr__(self, "_fields", fields)
        for k, v in zip(fields, row):
            object.__setattr__(self, k, v)

    def __getitem__(self, idx):
        return self._data[idx]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __bool__(self):
        return True

    def __repr__(self):
        pairs = ", ".join(f"{k}={v!r}" for k, v in zip(self._fields, self._data))
        return f"Row({pairs})"


def _row_factory(cursor, row):
    return _Row(cursor, row)


def obtener_conexion():
    db_path = _get_db_path()
    init_db(db_path)
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = _row_factory
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    except Exception as e:
        print("Error de conexión:", e)
        raise
