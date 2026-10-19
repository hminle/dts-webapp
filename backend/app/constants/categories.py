"""Category registries for the major-X / category-daily-yoy endpoints.

Each "major" endpoint aggregates a small set of upstream rows into a
single named bucket:

* **Spending / Receipt** — sums ``transaction_fytd_amt`` over a list of
  ``transaction_catg`` values from the ``deposits_withdrawals`` table,
  filtered by transaction type.
* **T-Bill interest** — sums ``adj_fytd_amt`` over a list of ``adj_type``
  values from ``adjustment_public_debt``.
* **IRS tax refunds** — sums ``tax_refund_fytd_amt`` over a list of
  ``tax_refund_type`` values from ``income_tax_refunds``.

Keeping the registries here (rather than next to the handlers) lets the
``/data/category-daily-yoy`` dispatcher resolve a category name without
re-importing each handler module, and lets the chunk-8 helpers iterate
the same data structure regardless of source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CategoryKind = Literal["spending", "receipt", "tbill", "irs_refund"]


@dataclass(frozen=True)
class CategoryDef:
    """A single named bucket and its component upstream identifiers."""

    name: str
    kind: CategoryKind
    components: tuple[str, ...]


# ── Spending (transaction_catg from deposits_withdrawals, Withdrawals) ──
MAJOR_SPENDING_CATEGORIES: tuple[CategoryDef, ...] = (
    CategoryDef(
        name="Social Security Benefits",
        kind="spending",
        components=(
            "SSA - Benefits Payments",
            "SSA - Supplemental Security Income",
            "Social Security Admin (SSA) - misc",
        ),
    ),
    CategoryDef(
        name="Medicare",
        kind="spending",
        components=(
            "HHS - Federal Hospital Insr Trust Fund",
            "HHS - Federal Supple Med Insr Trust Fund",
            "HHS - Medicare Prescription Drugs",
        ),
    ),
    CategoryDef(
        name="Medicaid",
        kind="spending",
        components=("HHS - Grants to States for Medicaid",),
    ),
    CategoryDef(
        name="Interest on Treasury Securities",
        kind="spending",
        components=("Interest on Treasury Securities",),
    ),
)


# ── Receipt (transaction_catg from deposits_withdrawals, Deposits) ─────
MAJOR_RECEIPT_CATEGORIES: tuple[CategoryDef, ...] = (
    CategoryDef(
        name="Employment & Withholding Tax",
        kind="receipt",
        components=("Taxes - Withheld Individual/FICA",),
    ),
    CategoryDef(
        name="Customs & Duties (Tariffs)",
        kind="receipt",
        components=(
            "DHS - Customs and Certain Excise Taxes",
            "DHS - Customs Duties, Taxes, and Fees",
        ),
    ),
)


# ── T-Bill interest (adj_type from adjustment_public_debt) ─────────────
# Each entry's ``components`` is a single-element tuple so we can keep a
# uniform shape across kinds while still surfacing the human-readable
# component name in API responses.
TBILL_INTEREST_COMPONENT_NAMES: dict[str, str] = {
    "Bills (-)": "Bills (-) Discount",
    "Bonds and Notes (-)": "Bonds and Notes (-) Discount",
}

TBILL_INTEREST_CATEGORY: CategoryDef = CategoryDef(
    name="T-Bill Interest",
    kind="tbill",
    components=tuple(TBILL_INTEREST_COMPONENT_NAMES.keys()),
)


# ── IRS Tax Refunds (tax_refund_type from income_tax_refunds) ──────────
IRS_REFUND_COMPONENT_NAMES: dict[str, str] = {
    "Taxes - Individual Tax Refunds (EFT)": "Individual Tax Refunds (EFT)",
    "Taxes - Business Tax Refunds (Checks)": "Business Tax Refunds (Checks)",
    "Taxes - Individual Tax Refunds (Checks)": "Individual Tax Refunds (Checks)",
    "Taxes - Business Tax Refunds (EFT)": "Business Tax Refunds (EFT)",
}

IRS_REFUND_CATEGORY: CategoryDef = CategoryDef(
    name="IRS Tax Refunds",
    kind="irs_refund",
    components=tuple(IRS_REFUND_COMPONENT_NAMES.keys()),
)


# ── Unified registry keyed by category display name ────────────────────
# Used by ``/data/category-daily-yoy`` to dispatch by category_name without
# branching on category_type.
CATEGORY_REGISTRY: dict[str, CategoryDef] = {
    cat.name: cat
    for cat in (
        *MAJOR_SPENDING_CATEGORIES,
        *MAJOR_RECEIPT_CATEGORIES,
        TBILL_INTEREST_CATEGORY,
        IRS_REFUND_CATEGORY,
    )
}
