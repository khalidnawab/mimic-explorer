"""Cohort criteria query engine — backed by DuckDB.

Takes a criteria JSON structure and returns matching patient/encounter pairs.
"""

from core.duckdb_queries import get_patients_for_criterion, execute_criteria  # noqa: F401
