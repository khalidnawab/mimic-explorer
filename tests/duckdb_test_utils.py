"""
DuckDB test utilities.

Provides a mixin that swaps the global DuckDB connection to an
in-memory database for test isolation.
"""
import duckdb
from core.duckdb_manager import set_connection, close_connection
from core.duckdb_schema import ensure_schema, drop_all_tables


class DuckDBTestMixin:
    """Mixin for TestCase classes that need DuckDB.

    Sets up an in-memory DuckDB connection in setUpClass,
    creates the schema, and tears down in tearDownClass.
    """

    @classmethod
    def _setup_duckdb(cls):
        """Create an in-memory DuckDB and set it as the global connection."""
        cls._duckdb_conn = duckdb.connect(':memory:')
        set_connection(cls._duckdb_conn)
        ensure_schema(cls._duckdb_conn)

    @classmethod
    def _teardown_duckdb(cls):
        """Close and reset the in-memory DuckDB connection."""
        try:
            cls._duckdb_conn.close()
        except Exception:
            pass
        set_connection(None)

    @classmethod
    def _reset_duckdb(cls):
        """Drop and recreate all tables for a clean slate."""
        drop_all_tables(cls._duckdb_conn)
        ensure_schema(cls._duckdb_conn)
