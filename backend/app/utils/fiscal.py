"""U.S. federal fiscal-year helpers (the fiscal year starts Oct 1)."""

from datetime import UTC, date, datetime


def current_fiscal_year(today: date | None = None) -> int:
    """Return the federal fiscal year containing ``today``.

    Examples:
        2026-09-30 -> 2026; 2026-10-01 -> 2027.
    """
    today = today or datetime.now(UTC).date()
    return today.year + 1 if today.month >= 10 else today.year


def fiscal_year_bounds(fiscal_year: int) -> tuple[date, date]:
    """Return the first and last calendar day of a fiscal year."""
    return date(fiscal_year - 1, 10, 1), date(fiscal_year, 9, 30)
