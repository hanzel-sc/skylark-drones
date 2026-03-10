"""
Pipeline Metrics Module.
Computes sales pipeline analytics using DuckDB on pandas DataFrames.
"""

import duckdb
import pandas as pd
from datetime import datetime
from typing import Optional

from utils.logging import get_logger
from utils.helpers import is_current_quarter, is_current_month

logger = get_logger(__name__)


class PipelineMetrics:
    """Compute pipeline-related business metrics from the Deals board."""

    def __init__(self, deals_df: pd.DataFrame):
        """
        Initialize with a cleaned deals DataFrame.

        Args:
            deals_df: Cleaned deals DataFrame from DataCleaner.
        """
        self.deals_df = deals_df
        self.con = duckdb.connect(":memory:")
        self.con.register("deals", self.deals_df)

    def pipeline_value_by_sector(self, status_filter: Optional[str] = "Open") -> pd.DataFrame:
        """
        Total pipeline value grouped by sector.

        Args:
            status_filter: Filter by deal status (default: "Open").

        Returns:
            DataFrame with sector and total_value columns.
        """
        query = """
            SELECT
                sector,
                COUNT(*) as deal_count,
                SUM(deal_value) as total_value,
                AVG(deal_value) as avg_value
            FROM deals
            WHERE deal_value > 0
        """
        if status_filter:
            query += f" AND deal_status = '{status_filter}'"
        query += " GROUP BY sector ORDER BY total_value DESC"

        result = self.con.execute(query).fetchdf()
        logger.info(f"Pipeline by sector: {len(result)} sectors")
        return result

    def pipeline_by_stage(self, status_filter: Optional[str] = "Open") -> pd.DataFrame:
        """
        Pipeline value grouped by deal stage.

        Args:
            status_filter: Optional deal status filter.

        Returns:
            DataFrame with deal_stage, deal_count, and total_value columns.
        """
        query = """
            SELECT
                deal_stage,
                COUNT(*) as deal_count,
                SUM(deal_value) as total_value
            FROM deals
            WHERE deal_value > 0
        """
        if status_filter:
            query += f" AND deal_status = '{status_filter}'"
        query += " GROUP BY deal_stage ORDER BY total_value DESC"

        result = self.con.execute(query).fetchdf()
        logger.info(f"Pipeline by stage: {len(result)} stages")
        return result

    def average_deal_size(self, status_filter: Optional[str] = None) -> float:
        """
        Calculate average deal size across the pipeline.

        Args:
            status_filter: Optional deal status filter.

        Returns:
            Average deal value as a float.
        """
        query = "SELECT AVG(deal_value) as avg_deal FROM deals WHERE deal_value > 0"
        if status_filter:
            query += f" AND deal_status = '{status_filter}'"

        result = self.con.execute(query).fetchone()
        avg = result[0] if result and result[0] else 0.0
        logger.info(f"Average deal size: {avg:,.2f}")
        return avg

    def deals_closing_this_month(self) -> pd.DataFrame:
        """
        Find deals with tentative close date in the current month.

        Returns:
            DataFrame of deals expected to close this month.
        """
        now = datetime.now()
        df = self.deals_df.copy()

        # Filter deals closing this month
        mask = df["tentative_close_date"].apply(is_current_month)
        result = df[mask & (df["deal_status"] == "Open")]

        logger.info(f"Deals closing this month: {len(result)}")
        return result[["deal_name", "sector", "deal_value", "deal_stage",
                       "closure_probability", "tentative_close_date"]].copy()

    def deals_closing_this_quarter(self, sector: Optional[str] = None) -> pd.DataFrame:
        """
        Find deals with tentative close date in the current quarter.

        Args:
            sector: Optional sector filter.

        Returns:
            DataFrame of deals closing this quarter.
        """
        df = self.deals_df.copy()
        mask = df["tentative_close_date"].apply(is_current_quarter)
        result = df[mask & (df["deal_status"] == "Open")]

        if sector:
            result = result[result["sector"] == sector.lower()]

        logger.info(f"Deals closing this quarter: {len(result)}")
        return result

    def total_pipeline_value(self, status_filter: Optional[str] = "Open") -> float:
        """
        Calculate total pipeline value.

        Args:
            status_filter: Optional deal status filter.

        Returns:
            Total pipeline value.
        """
        query = "SELECT SUM(deal_value) FROM deals WHERE deal_value > 0"
        if status_filter:
            query += f" AND deal_status = '{status_filter}'"

        result = self.con.execute(query).fetchone()
        total = result[0] if result and result[0] else 0.0
        logger.info(f"Total pipeline value: {total:,.2f}")
        return total

    def active_deals_count(self) -> int:
        """Count of active (Open) deals."""
        query = "SELECT COUNT(*) FROM deals WHERE deal_status = 'Open'"
        result = self.con.execute(query).fetchone()
        count = result[0] if result else 0
        logger.info(f"Active deals: {count}")
        return count

    def deal_creation_trend(self, months: int = 6) -> pd.DataFrame:
        """
        Deal creation counts over recent months.

        Args:
            months: Number of months to look back.

        Returns:
            DataFrame with month and deal_count columns.
        """
        df = self.deals_df.copy()
        df = df[df["created_date"].notna()]
        df["month"] = df["created_date"].apply(
            lambda x: x.strftime("%Y-%m") if x else None
        )
        df = df[df["month"].notna()]

        trend = df.groupby("month").size().reset_index(name="deal_count")
        trend = trend.sort_values("month").tail(months)

        logger.info(f"Deal creation trend: {len(trend)} months")
        return trend

    def pipeline_by_sector_and_quarter(self, sector: Optional[str] = None) -> pd.DataFrame:
        """
        Pipeline analysis filtered by sector for the current quarter.

        Args:
            sector: Optional sector filter.

        Returns:
            DataFrame with pipeline data.
        """
        df = self.deals_df.copy()
        df = df[df["deal_status"] == "Open"]
        df = df[df["deal_value"] > 0]

        if sector:
            df = df[df["sector"] == sector.lower()]

        # Filter current quarter
        df = df[df["tentative_close_date"].apply(is_current_quarter)]

        result = df.groupby("deal_stage").agg(
            deal_count=("deal_name", "count"),
            total_value=("deal_value", "sum"),
        ).reset_index().sort_values("total_value", ascending=False)

        return result

    def close(self):
        """Close the DuckDB connection."""
        self.con.close()
