"""Client for the Treasury Fiscal Data API, used only by ingestion.

Ported from the reference ``TreasuryAPIClient`` with one behavioral change that
matters for an all-or-nothing artifact: every failure raises. The reference
logged and returned whatever pages it had, which would publish a truncated file.
"""

import logging
import time
from datetime import date
from typing import Any

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.constants.endpoints import EndpointDef
from app.core.config import Settings

logger = logging.getLogger(__name__)

# (connect, read) seconds. The reference passed no timeout, so a stalled
# connection could hang a run forever.
REQUEST_TIMEOUT = (5, 60)

# Columns the reference coerced to numbers, verbatim; any *_amt / *_bal column
# is coerced too.
NUMERIC_COLUMNS = frozenset(
    {
        "open_today_bal",
        "close_today_bal",
        "open_month_bal",
        "open_fiscal_year_bal",
        "close_fiscal_year_bal",
        "today_bal",
        "month_bal",
        "fiscal_year_bal",
        "transaction_today_amt",
        "transaction_mtd_amt",
        "transaction_fytd_amt",
        "src_line_nbr",
        "record_fiscal_year",
        "record_fiscal_quarter",
        "record_calendar_year",
        "record_calendar_quarter",
        "record_calendar_month",
        "record_calendar_day",
        "deposit_today_amt",
        "deposit_mtd_amt",
        "deposit_fytd_amt",
        "withdrawal_today_amt",
        "withdrawal_mtd_amt",
        "withdrawal_fytd_amt",
        "adj_today_amt",
        "adj_mtd_amt",
        "adj_fytd_amt",
        "issue_today_amt",
        "issue_mtd_amt",
        "issue_fytd_amt",
        "redemption_today_amt",
        "redemption_mtd_amt",
        "redemption_fytd_amt",
        "intragov_holding_amt",
        "debt_held_public_amt",
        "statutory_debt_limit_amt",
        "tax_deposit_amt",
        "tax_refund_amt",
        "investment_today_amt",
        "investment_mtd_amt",
        "investment_fytd_amt",
    }
)


class TreasuryAPIError(RuntimeError):
    """A Treasury API request failed or returned something unusable."""


class TreasuryClient:
    """Fetches one DTS endpoint, page by page."""

    def __init__(self, endpoint: EndpointDef, settings: Settings) -> None:
        self.endpoint = endpoint
        self.url = settings.treasury_base_url + endpoint.api_path
        self.page_size = settings.api_page_size
        self.throttle = settings.api_throttle_time
        retry = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self._session = requests.Session()
        self._session.mount("https://", HTTPAdapter(max_retries=retry))

    def fetch_range(self, start: date, end: date) -> pd.DataFrame:
        """Fetch every row with ``start <= record_date <= end``."""
        return self._fetch(f"record_date:gte:{start},record_date:lte:{end}")

    def fetch_after(self, latest: date, today: date) -> pd.DataFrame:
        """Fetch every row with ``latest < record_date <= today``."""
        return self._fetch(f"record_date:gt:{latest},record_date:lte:{today}")

    def _fetch(self, filter_expr: str) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        page, total_pages = 1, 1
        while page <= total_pages:
            body = self._get_page(filter_expr, page)
            rows.extend(body["data"])
            if page == 1:
                total_pages = int(body.get("meta", {}).get("total-pages", 1) or 1)
            page += 1
            if page <= total_pages:
                time.sleep(self.throttle)
        logger.info(
            "%s: %d rows in %d page(s) for %s",
            self.endpoint.key,
            len(rows),
            total_pages,
            filter_expr,
        )
        return self.process(rows)

    def _get_page(self, filter_expr: str, page: int) -> dict[str, Any]:
        params = {
            "filter": filter_expr,
            "sort": "-record_date",
            "page[size]": self.page_size,
            "page[number]": page,
        }
        where = f"{self.endpoint.key} page {page}"
        try:
            response = self._session.get(
                self.url, params=params, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise TreasuryAPIError(f"{where}: {exc}") from exc
        if not isinstance(body, dict) or "data" not in body:
            raise TreasuryAPIError(f"{where}: response has no 'data' key")
        return body

    @staticmethod
    def process(rows: list[dict[str, Any]]) -> pd.DataFrame:
        """Turn API rows into a typed DataFrame (the reference ``process_data``).

        Zero rows is a valid answer and yields an empty frame.
        """
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        if "record_date" in df.columns:
            df["record_date"] = pd.to_datetime(df["record_date"])
        for col in df.columns:
            if col in NUMERIC_COLUMNS or col.endswith(("_amt", "_bal")):
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
