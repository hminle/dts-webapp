from datetime import date

from app.utils.fiscal import current_fiscal_year, fiscal_year_bounds


def test_september_belongs_to_the_same_fiscal_year() -> None:
    assert current_fiscal_year(date(2026, 9, 30)) == 2026


def test_october_starts_the_next_fiscal_year() -> None:
    assert current_fiscal_year(date(2026, 10, 1)) == 2027


def test_fiscal_year_bounds() -> None:
    assert fiscal_year_bounds(2026) == (date(2025, 10, 1), date(2026, 9, 30))
