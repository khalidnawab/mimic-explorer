"""
DuckDB connection manager.

Singleton connection for the clinical data database.
Thread-safe lazy initialization with support for test overrides.
"""
import threading

import duckdb
from django.conf import settings

_lock = threading.Lock()
_connection = None
_db_path = None  # None means use settings.DUCKDB_PATH


def get_db_path():
    """Return the path to the DuckDB database file."""
    if _db_path is not None:
        return _db_path
    return str(settings.DUCKDB_PATH)


def get_connection():
    """Return the singleton DuckDB connection, creating it if needed."""
    global _connection
    if _connection is not None:
        return _connection
    with _lock:
        if _connection is not None:
            return _connection
        path = get_db_path()
        _connection = duckdb.connect(path)
        return _connection


def close_connection():
    """Close the singleton DuckDB connection."""
    global _connection
    with _lock:
        if _connection is not None:
            try:
                _connection.close()
            except Exception:
                pass
            _connection = None


def set_connection(conn):
    """Swap in a custom connection (for tests). Pass None to reset."""
    global _connection
    with _lock:
        _connection = conn


def set_db_path(path):
    """Override the database path (for tests). Pass None to reset."""
    global _db_path
    _db_path = path
