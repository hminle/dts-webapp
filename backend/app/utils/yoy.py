"""Year-over-year alignment + FYTD aggregation helpers.

These helpers consolidate the logic that previously appeared four times,
near-identically, inside ``app/api/treasury.py`` for the four "major"
endpoints (major-spending, major-receipt, tbill-interest, irs-tax-refunds).

The aim is to factor out:

* ``latest_date_for_fy`` — locate the most recent ``record_date`` for a
  fiscal year, optionally constrained by extra filter columns (e.g.
  ``transaction_type='Withdrawals'``).
* ``find_aligned_previous_date`` — pick the previous-FY date that
  corresponds to a given current-FY date in either ``fiscal_day`` mode
  (matched by Day-N-of-FY) or ``calendar_date`` mode (matched by MM-DD).
* ``fetch_component_fytd`` / ``fetch_components_daily`` — read FYTD totals
  for one or more component keys on a given date / across an FY.
* ``yoy_change`` — common (delta, pct-or-None) computation.

Behavior is intentionally a bit-for-bit match of the legacy code paths so
the baseline snapshots stay green.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

ComparisonMode = Literal["fiscal_day", "calendar_date"]


@dataclass(frozen=True)
class FYTDSource:
    """How to read FYTD totals for a category-style endpoint.

    Attributes:
        table: source DuckDB table name.
        fytd_column: numeric column holding the FYTD value
            (e.g. ``transaction_fytd_amt``, ``adj_fytd_amt``).
        key_column: the column that stores the per-component identifier
            (e.g. ``transaction_catg``, ``adj_type``,
            ``tax_refund_type``).
        extra_filters: equality predicates applied to *latest-date*
            lookups only. The alignment lookup deliberately omits these,
            mirroring the legacy implementation.
    """

    table: str
    fytd_column: str
    key_column: str
    extra_filters: dict[str, str] = field(default_factory=dict)

    def filter_clause(self) -> tuple[str, list[Any]]:
        """SQL fragment + params for the configured ``extra_filters``."""
        if not self.extra_filters:
            return "", []
        clauses = " AND ".join(f"{col} = ?" for col in self.extra_filters)
        params = list(self.extra_filters.values())
        return f" AND {clauses}", params


def _to_iso_date(value: Any) -> str | None:
    """Best-effort conversion of a DuckDB date/datetime into ISO string."""
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)


def latest_date_for_fy(
    conn: Any,
    source: FYTDSource,
    fiscal_year: int,
) -> str | None:
    """Return the most recent ``record_date`` for ``fiscal_year``.

    Honors :attr:`FYTDSource.extra_filters`.
    """
    extra, extra_params = source.filter_clause()
    query = f"""
    SELECT MAX(record_date) AS max_date
    FROM {source.table}
    WHERE record_fiscal_year = ?{extra}
    """
    params: tuple[Any, ...] = (fiscal_year, *extra_params)
    result = conn.execute(query, params).fetchone()
    if result and result[0]:
        return _to_iso_date(result[0])
    return None


def fiscal_day_for_date(
    conn: Any,
    source: FYTDSource,
    fiscal_year: int,
    date: str,
) -> int:
    """Return the 1-based Day-of-fiscal-year for ``date`` in ``fiscal_year``.

    Computed as the count of distinct ``record_date`` values up to and
    including ``date``. Returns ``0`` when no rows exist.
    """
    query = f"""
    SELECT COUNT(DISTINCT record_date) AS day_num
    FROM {source.table}
    WHERE record_fiscal_year = ?
      AND record_date <= ?
    """
    result = conn.execute(query, (fiscal_year, date)).fetchone()
    return int(result[0]) if result and result[0] is not None else 0


def date_for_fiscal_day(
    conn: Any,
    source: FYTDSource,
    fiscal_year: int,
    day_of_fy: int,
) -> str | None:
    """Return the ``record_date`` corresponding to Day-N of ``fiscal_year``."""
    query = f"""
    WITH distinct_dates AS (
        SELECT DISTINCT record_date
        FROM {source.table}
        WHERE record_fiscal_year = ?
    ),
    ranked_dates AS (
        SELECT record_date,
               ROW_NUMBER() OVER (ORDER BY record_date) AS day_num
        FROM distinct_dates
    )
    SELECT record_date FROM ranked_dates WHERE day_num = ?
    """
    result = conn.execute(query, (fiscal_year, day_of_fy)).fetchone()
    if result and result[0]:
        return _to_iso_date(result[0])
    return None


def find_aligned_previous_date(
    conn: Any,
    *,
    source: FYTDSource,
    current_date: str,
    current_fy: int,
    previous_fy: int,
    mode: ComparisonMode,
) -> str | None:
    """Resolve the previous-FY date that pairs with ``current_date``.

    * ``calendar_date`` — match by MM-DD; if that exact date does not
      exist in the previous FY, fall back to the latest date ``<=`` it.
    * ``fiscal_day`` — match by Day-N-of-FY (per
      :func:`fiscal_day_for_date`).

    When neither lookup succeeds, falls back to the latest date in
    ``previous_fy`` (mirrors legacy behavior — caller decides whether
    that is acceptable).
    """
    if mode == "calendar_date":
        # Match by MM-DD with a fallback to latest <= date.
        current_mm_dd = current_date[5:10]
        expected_previous = f"{int(current_date[:4]) - 1}-{current_mm_dd}"

        exact = conn.execute(
            f"""
            SELECT record_date
            FROM {source.table}
            WHERE record_fiscal_year = ?
              AND record_date = ?
            LIMIT 1
            """,
            (previous_fy, expected_previous),
        ).fetchone()
        if exact and exact[0]:
            return _to_iso_date(exact[0])

        fallback = conn.execute(
            f"""
            SELECT MAX(record_date)
            FROM {source.table}
            WHERE record_fiscal_year = ?
              AND record_date <= ?
            """,
            (previous_fy, expected_previous),
        ).fetchone()
        if fallback and fallback[0]:
            return _to_iso_date(fallback[0])

        return latest_date_for_fy(conn, source, previous_fy)

    # mode == "fiscal_day"
    day_of_fy = fiscal_day_for_date(conn, source, current_fy, current_date)
    if day_of_fy <= 0:
        return latest_date_for_fy(conn, source, previous_fy)

    matched = date_for_fiscal_day(conn, source, previous_fy, day_of_fy)
    return matched or latest_date_for_fy(conn, source, previous_fy)


def fetch_component_fytd(
    conn: Any,
    source: FYTDSource,
    date: str,
    key: str,
) -> float:
    """FYTD amount for a single component on a single date (0.0 if missing).

    Honors :attr:`FYTDSource.extra_filters` so that, e.g., a deposits
    table query for a spending category does not accidentally match the
    deposits-side row of the same ``transaction_catg``.
    """
    extra, extra_params = source.filter_clause()
    query = f"""
    SELECT {source.fytd_column}
    FROM {source.table}
    WHERE record_date = ?
      AND {source.key_column} = ?{extra}
    """
    params: tuple[Any, ...] = (date, key, *extra_params)
    result = conn.execute(query, params).fetchone()
    return float(result[0]) if result and result[0] else 0.0


def fetch_components_daily(
    conn: Any,
    source: FYTDSource,
    fiscal_year: int,
    keys: list[str] | tuple[str, ...],
) -> list[tuple[str, float]]:
    """Per-day SUM of ``fytd_column`` over ``keys`` for ``fiscal_year``.

    Returns a list of ``(date_str, fytd_total)`` tuples ordered by date.
    """
    if not keys:
        return []

    placeholders = ", ".join("?" for _ in keys)
    extra, extra_params = source.filter_clause()
    query = f"""
    SELECT record_date, SUM({source.fytd_column}) AS fytd_amt
    FROM {source.table}
    WHERE record_fiscal_year = ?
      AND {source.key_column} IN ({placeholders}){extra}
    GROUP BY record_date
    ORDER BY record_date
    """
    params: tuple[Any, ...] = (fiscal_year, *keys, *extra_params)
    rows = conn.execute(query, params).fetchall()
    return [
        (_to_iso_date(r[0]) or "", float(r[1]) if r[1] is not None else 0.0)
        for r in rows
    ]


def yoy_change(
    current: float,
    previous: float,
) -> tuple[float, float | None]:
    """Return ``(delta, pct_change_or_None)``.

    Percent change is ``None`` when ``previous == 0`` to avoid division by
    zero. The denominator uses ``abs(previous)`` so signs are preserved
    even when previous is negative (matches legacy code).
    """
    delta = current - previous
    if previous == 0:
        return delta, None
    return delta, (delta / abs(previous)) * 100.0


def covered(available_from: date, day: str | None) -> bool:
    """Whether ``day`` (ISO date) is on or after ``available_from``.

    An empty or missing day is never covered.
    """
    return bool(day) and date.fromisoformat(day) >= available_from


def nullable_yoy(
    current: float | None, previous: float | None
) -> tuple[float | None, float | None]:
    """``yoy_change`` that passes ``None`` through when either side is missing."""
    if current is None or previous is None:
        return None, None
    return yoy_change(current, previous)
