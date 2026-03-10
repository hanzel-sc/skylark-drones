"""
Data Cleaning Pipeline for Monday BI Agent.
Comprehensive preprocessing: null handling, duplicate removal, outlier detection,
type enforcement, whitespace cleanup, sector/status normalization. 
"""

import re
import pandas as pd
import numpy as np
from typing import Optional

from config.settings import settings
from utils.logging import get_logger
from utils.helpers import parse_date_safe, safe_float

logger = get_logger(__name__)


class DataCleaner:
    """Cleans and normalizes messy business data from Monday.com boards."""

    def __init__(self):
        self.sector_aliases = settings.SECTOR_ALIASES
        self.warnings: list[str] = []

    # ==================================================================
    # Deals Pipeline
    # ==================================================================

    def clean_deals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full preprocessing pipeline for Deals board data."""
        logger.info(f"Cleaning deals data: {len(df)} rows, {len(df.columns)} columns")
        self.warnings = []
        df = df.copy()

        # 1. Standardize column names
        col_map = self._build_column_map(df.columns, {
            "deal_name": ["Deal Name", "item_name", "deal name", "Deal name"],
            "owner_code": ["Owner code", "owner code", "Owner Code"],
            "client_code": ["Client Code", "client code", "Client code"],
            "deal_status": ["Deal Status", "deal status"],
            "close_date": ["Close Date (A)", "close date", "Close Date"],
            "closure_probability": ["Closure Probability", "closure probability"],
            "deal_value": ["Masked Deal value", "masked deal value", "Deal Value", "deal value"],
            "tentative_close_date": ["Tentative Close Date", "tentative close date"],
            "deal_stage": ["Deal Stage", "deal stage"],
            "product_deal": ["Product deal", "product deal"],
            "sector": ["Sector/service", "sector/service", "Sector", "sector"],
            "created_date": ["Created Date", "created date"],
        })
        df = df.rename(columns=col_map)

        # 2. Drop fully empty rows and duplicates
        df = self._drop_empty_rows(df)
        df = self._remove_duplicates(df, subset=["deal_name", "client_code", "deal_value"])

        # 3. Remove header-like rows that got mixed in
        if "deal_status" in df.columns:
            df = df[~df["deal_status"].astype(str).isin(["Deal Status", "deal_status"])]

        # 4. Strip whitespace from all string columns
        df = self._strip_all_strings(df)

        # 5. Remove rows where deal_name is empty / null
        if "deal_name" in df.columns:
            df = df[df["deal_name"].astype(str).str.strip().ne("")]

        # 6. Normalize sectors
        if "sector" in df.columns:
            missing_sectors = df["sector"].isna().sum() + (df["sector"].astype(str).str.strip() == "").sum()
            if missing_sectors > 0:
                self.warnings.append(
                    f"Some deals are missing sector information. "
                    f"{missing_sectors} records affected. Results may be incomplete."
                )
            df["sector"] = df["sector"].apply(self._normalize_sector)

        # 7. Parse & validate dates
        for date_col in ["close_date", "tentative_close_date", "created_date"]:
            if date_col in df.columns:
                df[date_col] = df[date_col].apply(parse_date_safe)
                invalid_dates = df[date_col].isna().sum()
                if invalid_dates > 0:
                    logger.info(f"{date_col}: {invalid_dates} unparseable dates set to NaT")

        # 8. Clean numeric values & detect outliers
        if "deal_value" in df.columns:
            df["deal_value"] = df["deal_value"].apply(safe_float)
            # Replace negative values with 0 (corrupted data)
            negatives = (df["deal_value"] < 0).sum()
            if negatives > 0:
                self.warnings.append(f"{negatives} deals had negative values, reset to 0.")
                df.loc[df["deal_value"] < 0, "deal_value"] = 0.0
            # Flag extreme outliers (> 3 std devs from mean among non-zero)
            nonzero = df.loc[df["deal_value"] > 0, "deal_value"]
            if len(nonzero) > 10:
                mean_val, std_val = nonzero.mean(), nonzero.std()
                upper = mean_val + 3 * std_val
                outlier_count = (nonzero > upper).sum()
                if outlier_count > 0:
                    self.warnings.append(
                        f"{outlier_count} deal(s) with unusually high values detected "
                        f"(>{upper:,.0f}). These are kept but may skew averages."
                    )

        # 9. Normalize deal status & probability
        if "deal_status" in df.columns:
            df["deal_status"] = df["deal_status"].apply(self._normalize_deal_status)
        if "closure_probability" in df.columns:
            df["closure_probability"] = df["closure_probability"].apply(self._normalize_probability)

        # 10. Fill missing categoricals
        categorical_cols = ["deal_status", "deal_stage", "product_deal", "owner_code", "client_code"]
        df = self._fill_categoricals(df, categorical_cols)

        # 11. Enforce data types
        df = self._enforce_types(df, {
            "deal_value": "float64",
        })

        logger.info(f"Cleaned deals data: {len(df)} rows remaining")
        return df.reset_index(drop=True)

    # ==================================================================
    # Work Orders Pipeline
    # ==================================================================

    def clean_work_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full preprocessing pipeline for Work Orders board data."""
        logger.info(f"Cleaning work orders data: {len(df)} rows, {len(df.columns)} columns")
        self.warnings = []
        df = df.copy()

        # 1. Standardize column names
        col_map = self._build_column_map(df.columns, {
            "deal_name": ["Deal name masked", "item_name", "deal name masked"],
            "customer_code": ["Customer Name Code", "customer name code"],
            "serial": ["Serial #", "serial #"],
            "nature_of_work": ["Nature of Work", "nature of work"],
            "execution_status": ["Execution Status", "execution status"],
            "sector": ["Sector", "sector"],
            "type_of_work": ["Type of Work", "type of work"],
            "amount_total": [
                "Amount in Rupees (Excl of GST) (Masked)",
                "Amount in Rupees (Excl of GST.) (Masked)",
            ],
            "billed_value": [
                "Billed Value in Rupees (Masked)",
                "Billed Value in Rupees (Excl of GST.) (Masked)",
            ],
            "collected_amount": [
                "Collected Amount in Rupees",
                "Collected Amount in Rupees (Incl of GST.) (Masked)",
            ],
            "amount_to_be_billed": [
                "Amount to be billed",
                "Amount to be billed in Rs. (Exl. of GST) (Masked)",
            ],
            "amount_receivable": ["Amount Receivable", "Amount Receivable (Masked)"],
            "invoice_status": ["Invoice Status", "invoice status"],
            "expected_billing_month": ["Expected Billing Month", "expected billing month"],
            "actual_billing_month": ["Actual Billing Month", "actual billing month"],
            "wo_status": ["WO Status (billed)", "wo status (billed)"],
            "collection_status": ["Collection status", "collection status"],
            "billing_status": ["Billing Status", "billing status"],
            "probable_start_date": ["Probable Start Date", "probable start date"],
            "probable_end_date": ["Probable End Date", "probable end date"],
            "date_po_loi": ["Date of PO/LOI", "date of po/loi"],
            "bd_personnel": ["BD/KAM Personnel code", "bd/kam personnel code"],
            "last_invoice_date": ["Last invoice date", "last invoice date"],
            "software_platform": [
                "Is any Skylark software platform part of the contract",
                "Is any Skylark software platform part of the client deliverables in this deal?",
            ],
        })
        df = df.rename(columns=col_map)

        # 2. Drop fully empty rows and duplicates
        df = self._drop_empty_rows(df)
        df = self._remove_duplicates(df, subset=["deal_name", "serial", "amount_total"])

        # 3. Strip whitespace
        df = self._strip_all_strings(df)

        # 4. Normalize sectors
        if "sector" in df.columns:
            df["sector"] = df["sector"].apply(self._normalize_sector)

        # 5. Clean all numeric fields
        numeric_cols = [
            "amount_total", "billed_value", "collected_amount",
            "amount_to_be_billed", "amount_receivable",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].apply(safe_float)
                # Replace negative values
                neg_count = (df[col] < 0).sum()
                if neg_count > 0:
                    self.warnings.append(f"{neg_count} work orders had negative '{col}', reset to 0.")
                    df.loc[df[col] < 0, col] = 0.0

        # 6. Cross-field validation: receivable = billed - collected (if both exist)
        if all(c in df.columns for c in ["billed_value", "collected_amount", "amount_receivable"]):
            computed_receivable = df["billed_value"] - df["collected_amount"]
            mismatch = (
                (df["amount_receivable"] > 0) &
                (computed_receivable > 0) &
                ((df["amount_receivable"] - computed_receivable).abs() > 1)
            )
            mismatch_count = mismatch.sum()
            if mismatch_count > 0:
                logger.info(
                    f"{mismatch_count} work orders have receivable != billed - collected "
                    f"(likely due to GST differences)"
                )

        # 7. Check for missing receivables
        if "amount_receivable" in df.columns:
            missing_receivables = (df["amount_receivable"] == 0).sum()
            if missing_receivables > 0:
                self.warnings.append(
                    f"Receivable values missing for {missing_receivables} work orders. "
                    f"Results may be incomplete."
                )

        # 8. Parse dates
        date_cols = ["probable_start_date", "probable_end_date", "date_po_loi", "last_invoice_date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].apply(parse_date_safe)

        # 9. Normalize execution status
        if "execution_status" in df.columns:
            df["execution_status"] = df["execution_status"].fillna(settings.DEFAULT_CATEGORICAL_FILL)
            df["execution_status"] = df["execution_status"].str.strip()
            df["execution_status"] = df["execution_status"].apply(self._normalize_execution_status)

        # 10. Fill categoricals
        categorical_cols = [
            "nature_of_work", "type_of_work", "invoice_status",
            "wo_status", "collection_status", "billing_status",
        ]
        df = self._fill_categoricals(df, categorical_cols)

        # 11. Enforce data types
        df = self._enforce_types(df, {
            "amount_total": "float64",
            "billed_value": "float64",
            "collected_amount": "float64",
            "amount_to_be_billed": "float64",
            "amount_receivable": "float64",
        })

        logger.info(f"Cleaned work orders data: {len(df)} rows remaining")
        return df.reset_index(drop=True)

    # ==================================================================
    # Shared Preprocessing Utilities
    # ==================================================================

    def _drop_empty_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows that are entirely null or contain only whitespace."""
        before = len(df)
        df = df.dropna(how="all")
        # Also drop rows where every cell is empty string or whitespace
        str_cols = df.select_dtypes(include=["object"]).columns
        if len(str_cols) > 0:
            mask = df[str_cols].apply(lambda x: x.str.strip().eq("")).all(axis=1)
            df = df[~mask]
        dropped = before - len(df)
        if dropped > 0:
            logger.info(f"Dropped {dropped} fully empty rows")
        return df

    def _remove_duplicates(
        self, df: pd.DataFrame, subset: Optional[list[str]] = None
    ) -> pd.DataFrame:
        """Remove exact duplicate rows. If subset given, use those columns."""
        before = len(df)
        # Only use subset columns that actually exist
        if subset:
            subset = [c for c in subset if c in df.columns]
        if subset:
            df = df.drop_duplicates(subset=subset, keep="first")
        else:
            df = df.drop_duplicates(keep="first")
        dropped = before - len(df)
        if dropped > 0:
            self.warnings.append(f"{dropped} duplicate rows removed.")
            logger.info(f"Removed {dropped} duplicates")
        return df

    def _strip_all_strings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Strip leading/trailing whitespace from every string column."""
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        return df

    def _fill_categoricals(
        self, df: pd.DataFrame, cols: list[str]
    ) -> pd.DataFrame:
        """Fill missing categorical fields with default."""
        for col in cols:
            if col in df.columns:
                df[col] = df[col].fillna(settings.DEFAULT_CATEGORICAL_FILL)
                # Also replace empty strings
                df.loc[df[col].astype(str).str.strip() == "", col] = settings.DEFAULT_CATEGORICAL_FILL
        return df

    def _enforce_types(
        self, df: pd.DataFrame, type_map: dict[str, str]
    ) -> pd.DataFrame:
        """Force columns to specific dtypes, coercing errors to NaN/default."""
        for col, dtype in type_map.items():
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(dtype)
                except Exception as e:
                    logger.warning(f"Could not enforce type {dtype} on {col}: {e}")
        return df

    # ==================================================================
    # Normalizers
    # ==================================================================

    def _normalize_sector(self, sector: Optional[str]) -> str:
        """Normalize sector names to consistent lowercase values."""
        if pd.isna(sector) or sector is None or str(sector).strip() == "":
            return settings.DEFAULT_CATEGORICAL_FILL
        sector_lower = str(sector).strip().lower()
        # Remove special characters that may have leaked in
        sector_lower = re.sub(r'[^\w\s&/]', '', sector_lower).strip()
        return self.sector_aliases.get(sector_lower, sector_lower)

    def _normalize_deal_status(self, status: Optional[str]) -> str:
        """Normalize deal status values."""
        if pd.isna(status) or status is None or str(status).strip() == "":
            return settings.DEFAULT_CATEGORICAL_FILL
        status_clean = str(status).strip()
        status_map = {
            "open": "Open", "dead": "Dead", "won": "Won",
            "on hold": "On Hold", "lost": "Lost", "closed": "Won",
            "active": "Open", "inactive": "Dead",
        }
        return status_map.get(status_clean.lower(), status_clean)

    def _normalize_probability(self, prob: Optional[str]) -> str:
        """Normalize closure probability values."""
        if pd.isna(prob) or prob is None or str(prob).strip() == "":
            return settings.DEFAULT_CATEGORICAL_FILL
        prob_clean = str(prob).strip().lower()
        prob_map = {"high": "High", "medium": "Medium", "low": "Low"}
        return prob_map.get(prob_clean, prob_clean.title())

    def _normalize_execution_status(self, status: Optional[str]) -> str:
        """Normalize execution status with common variant handling."""
        if pd.isna(status) or status is None or str(status).strip() == "":
            return settings.DEFAULT_CATEGORICAL_FILL
        s = str(status).strip().lower()
        status_map = {
            "completed": "Completed",
            "done": "Completed",
            "ongoing": "Ongoing",
            "in progress": "Ongoing",
            "not started": "Not Started",
            "pending": "Not Started",
            "executed until c...": "Executed until current",
            "executed until c": "Executed until current",
        }
        # Partial match for "executed until c..."
        if s.startswith("executed until"):
            return "Executed until current"
        return status_map.get(s, status.strip())

    # ==================================================================
    # Column Mapping Builder
    # ==================================================================

    def _build_column_map(self, existing_cols: pd.Index, target_map: dict) -> dict:
        """Build a column rename mapping from possible aliases."""
        rename_map = {}
        existing_lower = {col.lower().strip(): col for col in existing_cols}
        for target_name, aliases in target_map.items():
            for alias in aliases:
                alias_lower = alias.lower().strip()
                if alias_lower in existing_lower:
                    rename_map[existing_lower[alias_lower]] = target_name
                    break
        return rename_map

    def get_warnings(self) -> list[str]:
        """Return any data quality warnings generated during cleaning."""
        return self.warnings
