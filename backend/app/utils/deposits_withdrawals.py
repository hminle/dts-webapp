"""
Utility functions for calculating daily net transfers from deposits & withdrawals data.

This module provides functions to calculate various treasury metrics from
deposits_withdrawals table data.
"""

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def calculate_daily_net_transfers(df: pd.DataFrame, date: str) -> dict[str, Any] | None:
    """
    Calculate daily net transfer metrics from deposits & withdrawals for one date.

    This function extracts and calculates:
    - Total Deposits (excluding Public Debt Cash Issues)
    - Total Withdrawals (excluding Public Debt Cash Redemptions)
    - Net Flow (Total Withdrawals - Total Deposits)
    - Leading Flow (Total Withdrawals)

    Args:
        df: DataFrame containing deposits_withdrawals data for the date
        date: Date in YYYY-MM-DD format

    Returns:
        Dictionary with calculated metrics, or None if data is incomplete

    Raises:
        ValueError: If required data is missing
    """
    if df.empty:
        logger.warning(f"No data provided for date {date}")
        return None

    # Debug: Log unique account types in the data
    unique_account_types = df["account_type"].unique().tolist()
    logger.debug(f"Date {date} has account types: {unique_account_types}")

    try:
        # 1. Treasury General Account Total Deposits
        # First, try to get the pre-aggregated row
        tga_deposits_row = df[
            df["account_type"] == "Treasury General Account Total Deposits"
        ]

        if not tga_deposits_row.empty:
            # Use pre-aggregated data
            tga_deposits_today = float(
                tga_deposits_row["transaction_today_amt"].iloc[0] or 0
            )
            tga_deposits_mtd = float(
                tga_deposits_row["transaction_mtd_amt"].iloc[0] or 0
            )
            tga_deposits_fytd = float(
                tga_deposits_row["transaction_fytd_amt"].iloc[0] or 0
            )
        else:
            # Calculate ourselves: sum all TGA Deposits rows
            logger.info(
                f"Pre-aggregated TGA Total Deposits not found for {date}, "
                "calculating from individual rows"
            )

            # Try Treasury General Account (TGA) first
            tga_deposits_rows = df[
                (df["account_type"] == "Treasury General Account (TGA)")
                & (df["transaction_type"] == "Deposits")
            ]

            # If no TGA rows, try Federal Reserve Account
            if tga_deposits_rows.empty:
                logger.debug(
                    f"No TGA rows found, trying Federal Reserve Account for {date}"
                )
                tga_deposits_rows = df[
                    (df["account_type"] == "Federal Reserve Account")
                    & (df["transaction_type"] == "Deposits")
                ]

            if tga_deposits_rows.empty:
                logger.warning(
                    f"No Deposits data found for {date} in either TGA or "
                    "Federal Reserve Account"
                )
                return None

            tga_deposits_today = float(
                tga_deposits_rows["transaction_today_amt"].sum() or 0
            )
            tga_deposits_mtd = float(
                tga_deposits_rows["transaction_mtd_amt"].sum() or 0
            )
            tga_deposits_fytd = float(
                tga_deposits_rows["transaction_fytd_amt"].sum() or 0
            )

        # 2. Treasury General Account Total Withdrawals
        # First, try to get the pre-aggregated row
        tga_withdrawals_row = df[
            df["account_type"] == "Treasury General Account Total Withdrawals"
        ]

        if not tga_withdrawals_row.empty:
            # Use pre-aggregated data
            tga_withdrawals_today = float(
                tga_withdrawals_row["transaction_today_amt"].iloc[0] or 0
            )
            tga_withdrawals_mtd = float(
                tga_withdrawals_row["transaction_mtd_amt"].iloc[0] or 0
            )
            tga_withdrawals_fytd = float(
                tga_withdrawals_row["transaction_fytd_amt"].iloc[0] or 0
            )
        else:
            # Calculate ourselves: sum all TGA Withdrawals rows
            logger.info(
                f"Pre-aggregated TGA Total Withdrawals not found for {date}, "
                "calculating from individual rows"
            )

            # Try Treasury General Account (TGA) first
            tga_withdrawals_rows = df[
                (df["account_type"] == "Treasury General Account (TGA)")
                & (df["transaction_type"] == "Withdrawals")
            ]

            # If no TGA rows, try Federal Reserve Account
            if tga_withdrawals_rows.empty:
                logger.debug(
                    f"No TGA rows found, trying Federal Reserve Account for {date}"
                )
                tga_withdrawals_rows = df[
                    (df["account_type"] == "Federal Reserve Account")
                    & (df["transaction_type"] == "Withdrawals")
                ]

            if tga_withdrawals_rows.empty:
                logger.warning(
                    f"No Withdrawals data found for {date} in either TGA or "
                    "Federal Reserve Account"
                )
                return None

            tga_withdrawals_today = float(
                tga_withdrawals_rows["transaction_today_amt"].sum() or 0
            )
            tga_withdrawals_mtd = float(
                tga_withdrawals_rows["transaction_mtd_amt"].sum() or 0
            )
            tga_withdrawals_fytd = float(
                tga_withdrawals_rows["transaction_fytd_amt"].sum() or 0
            )

        # 3. Public Debt Cash Issues (Table IIIB) - TGA, then Federal Reserve Acct
        debt_issues_row = df[
            (df["account_type"] == "Treasury General Account (TGA)")
            & (df["transaction_catg"] == "Public Debt Cash Issues (Table IIIB)")
        ]
        if debt_issues_row.empty:
            debt_issues_row = df[
                (df["account_type"] == "Federal Reserve Account")
                & (df["transaction_catg"] == "Public Debt Cash Issues (Table IIIB)")
            ]

        # 4. Public Debt Cash Redemptions (Table IIIB) - TGA, then Federal Reserve Acct
        debt_redemp_row = df[
            (df["account_type"] == "Treasury General Account (TGA)")
            & (df["transaction_catg"] == "Public Debt Cash Redemp. (Table IIIB)")
        ]
        if debt_redemp_row.empty:
            debt_redemp_row = df[
                (df["account_type"] == "Federal Reserve Account")
                & (df["transaction_catg"] == "Public Debt Cash Redemp. (Table IIIB)")
            ]

        # Extract debt values
        debt_issues_today = (
            float(debt_issues_row["transaction_today_amt"].iloc[0])
            if not debt_issues_row.empty
            else 0.0
        )
        debt_issues_mtd = (
            float(debt_issues_row["transaction_mtd_amt"].iloc[0])
            if not debt_issues_row.empty
            else 0.0
        )
        debt_issues_fytd = (
            float(debt_issues_row["transaction_fytd_amt"].iloc[0])
            if not debt_issues_row.empty
            else 0.0
        )

        debt_redemp_today = (
            float(debt_redemp_row["transaction_today_amt"].iloc[0])
            if not debt_redemp_row.empty
            else 0.0
        )
        debt_redemp_mtd = (
            float(debt_redemp_row["transaction_mtd_amt"].iloc[0])
            if not debt_redemp_row.empty
            else 0.0
        )
        debt_redemp_fytd = (
            float(debt_redemp_row["transaction_fytd_amt"].iloc[0])
            if not debt_redemp_row.empty
            else 0.0
        )

        # Calculate totals (matching Streamlit logic)
        total_deposits_today = tga_deposits_today - debt_issues_today
        total_deposits_mtd = tga_deposits_mtd - debt_issues_mtd
        total_deposits_fytd = tga_deposits_fytd - debt_issues_fytd

        total_withdrawals_today = tga_withdrawals_today - debt_redemp_today
        total_withdrawals_mtd = tga_withdrawals_mtd - debt_redemp_mtd
        total_withdrawals_fytd = tga_withdrawals_fytd - debt_redemp_fytd

        # Net Government Transfers = Total Withdrawals - Total Deposits
        net_flow_today = total_withdrawals_today - total_deposits_today
        net_flow_mtd = total_withdrawals_mtd - total_deposits_mtd
        net_flow_fytd = total_withdrawals_fytd - total_deposits_fytd

        # Leading Flow = Total Withdrawals
        leading_flow = total_withdrawals_today

        return {
            "date": date,
            "tga_total_deposits_today": tga_deposits_today,
            "tga_total_withdrawals_today": tga_withdrawals_today,
            "public_debt_issues_today": debt_issues_today,
            "public_debt_redemptions_today": debt_redemp_today,
            "total_deposits_today": total_deposits_today,
            "total_withdrawals_today": total_withdrawals_today,
            "net_flow_today": net_flow_today,
            "leading_flow": leading_flow,
            "tga_total_deposits_mtd": tga_deposits_mtd,
            "tga_total_withdrawals_mtd": tga_withdrawals_mtd,
            "public_debt_issues_mtd": debt_issues_mtd,
            "public_debt_redemptions_mtd": debt_redemp_mtd,
            "total_deposits_mtd": total_deposits_mtd,
            "total_withdrawals_mtd": total_withdrawals_mtd,
            "net_flow_mtd": net_flow_mtd,
            "tga_total_deposits_fytd": tga_deposits_fytd,
            "tga_total_withdrawals_fytd": tga_withdrawals_fytd,
            "public_debt_issues_fytd": debt_issues_fytd,
            "public_debt_redemptions_fytd": debt_redemp_fytd,
            "total_deposits_fytd": total_deposits_fytd,
            "total_withdrawals_fytd": total_withdrawals_fytd,
            "net_flow_fytd": net_flow_fytd,
        }

    except Exception as e:
        logger.exception(f"Error calculating daily net transfers for {date}: {e}")
        return None
