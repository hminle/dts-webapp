"""The single registry of Treasury DTS endpoints.

Each key is also the DuckDB table name. Paths and display names come from the
reference app's ``TREASURY_ENDPOINTS`` and ``get_available_endpoints``, which
were two of its three parallel mappings; this module replaces all three.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointDef:
    key: str
    api_path: str
    display_name: str


ENDPOINTS: dict[str, EndpointDef] = {
    d.key: d
    for d in (
        EndpointDef(
            "operating_cash_balance",
            "/v1/accounting/dts/operating_cash_balance",
            "Operating Cash Balance",
        ),
        EndpointDef(
            "deposits_withdrawals",
            "/v1/accounting/dts/deposits_withdrawals_operating_cash",
            "Deposits & Withdrawals",
        ),
        EndpointDef(
            "public_debt_transactions",
            "/v1/accounting/dts/public_debt_transactions",
            "Public Debt Transactions",
        ),
        EndpointDef(
            "adjustment_public_debt",
            "/v1/accounting/dts/adjustment_public_debt_transactions_cash_basis",
            "Public Debt Adjustments",
        ),
        EndpointDef(
            "debt_subject_to_limit",
            "/v1/accounting/dts/debt_subject_to_limit",
            "Debt Subject to Limit",
        ),
        EndpointDef(
            "inter_agency_tax_transfers",
            "/v1/accounting/dts/inter_agency_tax_transfers",
            "Inter-Agency Tax Transfers",
        ),
        EndpointDef(
            "income_tax_refunds",
            "/v1/accounting/dts/income_tax_refunds_issued",
            "Income Tax Refunds",
        ),
        EndpointDef(
            "federal_tax_deposits",
            "/v1/accounting/dts/federal_tax_deposits",
            "Federal Tax Deposits",
        ),
        EndpointDef(
            "short_term_cash_investments",
            "/v1/accounting/dts/short_term_cash_investments",
            "Short-Term Cash Investments",
        ),
    )
}

ENDPOINT_TABLES: tuple[str, ...] = tuple(ENDPOINTS)
DERIVED_TABLES: tuple[str, ...] = ("daily_net_transfers",)
ALL_TABLES: tuple[str, ...] = ENDPOINT_TABLES + DERIVED_TABLES
ACCOUNT_TYPE_TABLES: tuple[str, ...] = (
    "operating_cash_balance",
    "deposits_withdrawals",
)


def table_for(key: str) -> str:
    """Return the table for an endpoint key.

    Raises:
        ValueError: If the key is not a known endpoint. The reference app fell
            back to ``deposits_withdrawals`` here, silently writing to or
            reading from the wrong table.
    """
    if key not in ENDPOINTS:
        raise ValueError(f"Unknown Treasury endpoint key: {key!r}")
    return key
