"""DuckDB schema for the Treasury artifact.

Ported verbatim from the reference app's ``DuckDBConnection._init_schema``
(dts-analysis ``app/duckdb_database.py``). Ingestion calls it to create a fresh
artifact; tests call it to build seeded fixtures with the real schema.
"""

import duckdb

from app.constants.endpoints import ALL_TABLES

SCHEMA_VERSION = "1"


def create_schema(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the metadata table, endpoint tables, derived table and indexes.

    Idempotent: every statement is ``IF NOT EXISTS``.
    """
    # Create metadata table first
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key VARCHAR PRIMARY KEY,
            value VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create sequences for auto-incrementing IDs
    sequences = [
        "operating_cash_balance_id_seq",
        "deposits_withdrawals_id_seq",
        "public_debt_transactions_id_seq",
        "adjustment_public_debt_id_seq",
        "debt_subject_to_limit_id_seq",
        "inter_agency_tax_transfers_id_seq",
        "income_tax_refunds_id_seq",
        "federal_tax_deposits_id_seq",
        "short_term_cash_investments_id_seq",
        "daily_net_transfers_id_seq",
    ]

    for seq in sequences:
        conn.execute(f"CREATE SEQUENCE IF NOT EXISTS {seq} START 1")

    # 1. Operating Cash Balance (16 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS operating_cash_balance (
            id INTEGER PRIMARY KEY DEFAULT nextval('operating_cash_balance_id_seq'),
            record_date DATE NOT NULL,
            account_type VARCHAR,
            close_today_bal DOUBLE,
            open_today_bal DOUBLE,
            open_month_bal DOUBLE,
            open_fiscal_year_bal DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            sub_table_name VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Deposits & Withdrawals (17 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deposits_withdrawals (
            id INTEGER PRIMARY KEY DEFAULT nextval('deposits_withdrawals_id_seq'),
            record_date DATE NOT NULL,
            account_type VARCHAR,
            transaction_type VARCHAR,
            transaction_catg VARCHAR,
            transaction_catg_desc VARCHAR,
            transaction_today_amt DOUBLE,
            transaction_mtd_amt DOUBLE,
            transaction_fytd_amt DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Public Debt Transactions (17 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS public_debt_transactions (
            id INTEGER PRIMARY KEY DEFAULT nextval('public_debt_transactions_id_seq'),
            record_date DATE NOT NULL,
            transaction_type VARCHAR,
            security_market VARCHAR,
            security_type VARCHAR,
            security_type_desc VARCHAR,
            transaction_today_amt DOUBLE,
            transaction_mtd_amt DOUBLE,
            transaction_fytd_amt DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Adjustment to Public Debt (17 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS adjustment_public_debt (
            id INTEGER PRIMARY KEY DEFAULT nextval('adjustment_public_debt_id_seq'),
            record_date DATE NOT NULL,
            transaction_type VARCHAR,
            adj_type VARCHAR,
            adj_type_desc VARCHAR,
            adj_today_amt DOUBLE,
            adj_mtd_amt DOUBLE,
            adj_fytd_amt DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            sub_table_name VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Debt Subject to Limit (17 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS debt_subject_to_limit (
            id INTEGER PRIMARY KEY DEFAULT nextval('debt_subject_to_limit_id_seq'),
            record_date DATE NOT NULL,
            debt_catg VARCHAR,
            debt_catg_desc VARCHAR,
            close_today_bal DOUBLE,
            open_today_bal DOUBLE,
            open_month_bal DOUBLE,
            open_fiscal_year_bal DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            sub_table_name VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Inter-Agency Tax Transfers (15 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inter_agency_tax_transfers (
            id INTEGER PRIMARY KEY DEFAULT nextval('inter_agency_tax_transfers_id_seq'),
            record_date DATE NOT NULL,
            classification VARCHAR,
            today_amt DOUBLE,
            mtd_amt DOUBLE,
            fytd_amt DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            sub_table_name VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. Income Tax Refunds (16 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS income_tax_refunds (
            id INTEGER PRIMARY KEY DEFAULT nextval('income_tax_refunds_id_seq'),
            record_date DATE NOT NULL,
            tax_refund_type VARCHAR,
            tax_refund_type_desc VARCHAR,
            tax_refund_today_amt DOUBLE,
            tax_refund_mtd_amt DOUBLE,
            tax_refund_fytd_amt DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            sub_table_name VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 8. Federal Tax Deposits (16 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS federal_tax_deposits (
            id INTEGER PRIMARY KEY DEFAULT nextval('federal_tax_deposits_id_seq'),
            record_date DATE NOT NULL,
            tax_deposit_type VARCHAR,
            tax_deposit_type_desc VARCHAR,
            tax_deposit_today_amt DOUBLE,
            tax_deposit_mtd_amt DOUBLE,
            tax_deposit_fytd_amt DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            sub_table_name VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 9. Short-Term Cash Investments (17 columns from API)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS short_term_cash_investments (
            id INTEGER PRIMARY KEY
                DEFAULT nextval('short_term_cash_investments_id_seq'),
            record_date DATE NOT NULL,
            transaction_type VARCHAR,
            transaction_type_desc VARCHAR,
            depositary_type_a_amt DOUBLE,
            depositary_type_b_amt DOUBLE,
            depositary_type_c_amt DOUBLE,
            total_amt DOUBLE,
            table_nbr VARCHAR,
            table_nm VARCHAR,
            sub_table_name VARCHAR,
            src_line_nbr INTEGER,
            record_fiscal_year INTEGER,
            record_fiscal_quarter INTEGER,
            record_calendar_year INTEGER,
            record_calendar_quarter INTEGER,
            record_calendar_month INTEGER,
            record_calendar_day INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 10. Daily Net Transfers (calculated from Deposits & Withdrawals)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_net_transfers (
            id INTEGER PRIMARY KEY DEFAULT nextval('daily_net_transfers_id_seq'),
            record_date DATE NOT NULL,
            record_fiscal_year INTEGER NOT NULL,
            day_of_fiscal_year INTEGER NOT NULL,
            tga_total_deposits_today DOUBLE,
            tga_total_withdrawals_today DOUBLE,
            public_debt_issues_today DOUBLE,
            public_debt_redemptions_today DOUBLE,
            total_deposits_today DOUBLE,
            total_withdrawals_today DOUBLE,
            net_flow_today DOUBLE,
            leading_flow DOUBLE,
            tga_total_deposits_mtd DOUBLE,
            tga_total_withdrawals_mtd DOUBLE,
            public_debt_issues_mtd DOUBLE,
            public_debt_redemptions_mtd DOUBLE,
            total_deposits_mtd DOUBLE,
            total_withdrawals_mtd DOUBLE,
            net_flow_mtd DOUBLE,
            tga_total_deposits_fytd DOUBLE,
            tga_total_withdrawals_fytd DOUBLE,
            public_debt_issues_fytd DOUBLE,
            public_debt_redemptions_fytd DOUBLE,
            total_deposits_fytd DOUBLE,
            total_withdrawals_fytd DOUBLE,
            net_flow_fytd DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(record_date)
        )
    """)

    # Create indexes for each table
    for table in ALL_TABLES:
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_record_date
            ON {table}(record_date)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_fiscal_year
            ON {table}(record_fiscal_year)
        """)
