"""
Financial Metrics Module.
Computes billing, collection, and receivables analytics.
"""

import duckdb
import pandas as pd
from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)


class FinancialMetrics:
    """Compute financial metrics from the Work Orders board."""

    def __init__(self, work_orders_df: pd.DataFrame):
        """
        Initialize with a cleaned work orders DataFrame.

        Args:
            work_orders_df: Cleaned work orders DataFrame.
        """
        self.wo_df = work_orders_df
        self.con = duckdb.connect(":memory:")
        self.con.register("work_orders", self.wo_df)

    def total_billed(self) -> float:
        """
        Calculate total billed value across all work orders.

        Returns:
            Total billed amount.
        """
        query = "SELECT SUM(billed_value) FROM work_orders WHERE billed_value > 0"
        result = self.con.execute(query).fetchone()
        total = result[0] if result and result[0] else 0.0
        logger.info(f"Total billed: {total:,.2f}")
        return total

    def total_collected(self) -> float:
        """
        Calculate total collected amount across all work orders.

        Returns:
            Total collected amount.
        """
        query = "SELECT SUM(collected_amount) FROM work_orders WHERE collected_amount > 0"
        result = self.con.execute(query).fetchone()
        total = result[0] if result and result[0] else 0.0
        logger.info(f"Total collected: {total:,.2f}")
        return total

    def receivable_amount(self) -> float:
        """
        Calculate total outstanding receivable amount.

        Returns:
            Total receivable amount.
        """
        query = "SELECT SUM(amount_receivable) FROM work_orders WHERE amount_receivable > 0"
        result = self.con.execute(query).fetchone()
        total = result[0] if result and result[0] else 0.0
        logger.info(f"Total receivable: {total:,.2f}")
        return total

    def billing_vs_collection(self) -> pd.DataFrame:
        """
        Compare billing and collection amounts by sector.

        Returns:
            DataFrame with sector, billed, collected, and receivable columns.
        """
        query = """
            SELECT
                sector,
                SUM(billed_value) as billed,
                SUM(collected_amount) as collected,
                SUM(amount_receivable) as receivable,
                SUM(amount_to_be_billed) as to_be_billed
            FROM work_orders
            WHERE sector != 'unknown'
            GROUP BY sector
            ORDER BY billed DESC
        """
        result = self.con.execute(query).fetchdf()
        logger.info(f"Billing vs collection: {len(result)} sectors")
        return result

    def collection_rate(self) -> float:
        """
        Calculate overall collection rate (collected / billed).

        Returns:
            Collection rate as a percentage.
        """
        billed = self.total_billed()
        collected = self.total_collected()
        rate = (collected / billed * 100) if billed > 0 else 0.0
        logger.info(f"Collection rate: {rate:.1f}%")
        return round(rate, 1)

    def receivables_by_sector(self) -> pd.DataFrame:
        """
        Outstanding receivables grouped by sector.

        Returns:
            DataFrame with sector and receivable_amount columns.
        """
        query = """
            SELECT
                sector,
                SUM(amount_receivable) as receivable_amount,
                COUNT(*) as wo_count
            FROM work_orders
            WHERE amount_receivable > 0
            GROUP BY sector
            ORDER BY receivable_amount DESC
        """
        result = self.con.execute(query).fetchdf()
        return result

    def financial_summary(self) -> dict:
        """
        Generate a complete financial summary.

        Returns:
            Dict with all key financial metrics.
        """
        billed = self.total_billed()
        collected = self.total_collected()
        receivable = self.receivable_amount()

        summary = {
            "total_billed": billed,
            "total_collected": collected,
            "total_receivable": receivable,
            "collection_rate": round((collected / billed * 100) if billed > 0 else 0.0, 1),
            "outstanding_ratio": round((receivable / billed * 100) if billed > 0 else 0.0, 1),
        }
        logger.info(f"Financial summary generated: {summary}")
        return summary

    def close(self):
        """Close the DuckDB connection."""
        self.con.close()
