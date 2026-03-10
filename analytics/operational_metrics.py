"""
Operational Metrics Module.
Computes work order and operational analytics using DuckDB.
"""

import duckdb
import pandas as pd
from typing import Optional

from utils.logging import get_logger

logger = get_logger(__name__)


class OperationalMetrics:
    """Compute operational metrics from the Work Orders board."""

    def __init__(self, work_orders_df: pd.DataFrame):
        """
        Initialize with a cleaned work orders DataFrame.

        Args:
            work_orders_df: Cleaned work orders DataFrame.
        """
        self.wo_df = work_orders_df
        self.con = duckdb.connect(":memory:")
        self.con.register("work_orders", self.wo_df)

    def work_orders_by_sector(self) -> pd.DataFrame:
        """
        Count and value of work orders grouped by sector.

        Returns:
            DataFrame with sector, order_count, and total_value columns.
        """
        query = """
            SELECT
                sector,
                COUNT(*) as order_count,
                SUM(amount_total) as total_value
            FROM work_orders
            GROUP BY sector
            ORDER BY order_count DESC
        """
        result = self.con.execute(query).fetchdf()
        logger.info(f"Work orders by sector: {len(result)} sectors")
        return result

    def execution_status_distribution(self) -> pd.DataFrame:
        """
        Distribution of work order execution statuses.

        Returns:
            DataFrame with execution_status and count columns.
        """
        query = """
            SELECT
                execution_status,
                COUNT(*) as count
            FROM work_orders
            WHERE execution_status != 'unknown'
            GROUP BY execution_status
            ORDER BY count DESC
        """
        result = self.con.execute(query).fetchdf()
        logger.info(f"Execution status distribution: {len(result)} statuses")
        return result

    def billing_completion_rate(self) -> dict:
        """
        Calculate billing completion rate.

        Returns:
            Dict with total_amount, billed_amount, completion_rate, and unbilled.
        """
        query = """
            SELECT
                SUM(amount_total) as total_amount,
                SUM(billed_value) as billed_amount,
                SUM(amount_to_be_billed) as unbilled_amount
            FROM work_orders
            WHERE amount_total > 0
        """
        result = self.con.execute(query).fetchone()
        total = result[0] if result[0] else 0.0
        billed = result[1] if result[1] else 0.0
        unbilled = result[2] if result[2] else 0.0

        completion_rate = (billed / total * 100) if total > 0 else 0.0

        metrics = {
            "total_amount": total,
            "billed_amount": billed,
            "unbilled_amount": unbilled,
            "completion_rate": round(completion_rate, 1),
        }
        logger.info(f"Billing completion rate: {metrics['completion_rate']}%")
        return metrics

    def active_work_orders(self) -> int:
        """Count of active (Open/Ongoing) work orders."""
        if "wo_status" in self.wo_df.columns:
            active = self.wo_df[
                self.wo_df["wo_status"].isin(["Open", "open", "unknown"])
            ].shape[0]
        else:
            active = len(self.wo_df)

        # Also consider execution_status
        if "execution_status" in self.wo_df.columns:
            ongoing = self.wo_df[
                self.wo_df["execution_status"].isin([
                    "Ongoing", "Not Started", "Executed until current month",
                    "Partial Completed", "Pause / struck", "Details pending from Client"
                ])
            ].shape[0]
            active = max(active, ongoing)

        logger.info(f"Active work orders: {active}")
        return active

    def work_orders_by_type(self) -> pd.DataFrame:
        """
        Distribution of work orders by nature of work.

        Returns:
            DataFrame with nature_of_work and count columns.
        """
        query = """
            SELECT
                nature_of_work,
                COUNT(*) as count,
                SUM(amount_total) as total_value
            FROM work_orders
            WHERE nature_of_work != 'unknown'
            GROUP BY nature_of_work
            ORDER BY count DESC
        """
        result = self.con.execute(query).fetchdf()
        return result

    def work_orders_by_status(self) -> pd.DataFrame:
        """
        Distribution of work orders by billing status.

        Returns:
            DataFrame with billing_status and count columns.
        """
        if "billing_status" not in self.wo_df.columns:
            return pd.DataFrame()

        query = """
            SELECT
                billing_status,
                COUNT(*) as count
            FROM work_orders
            WHERE billing_status != 'unknown' AND billing_status != ''
            GROUP BY billing_status
            ORDER BY count DESC
        """
        result = self.con.execute(query).fetchdf()
        return result

    def close(self):
        """Close the DuckDB connection."""
        self.con.close()
