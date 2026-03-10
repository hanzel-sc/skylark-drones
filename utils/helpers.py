"""
Helper utilities for Monday BI Agent.
Common functions used across multiple modules.
"""

import re
from datetime import datetime, date
from typing import Optional, Any

import pandas as pd


def parse_date_safe(date_str: Any) -> Optional[datetime]:
    """
    Safely parse a date string into a datetime object.
    Returns None for invalid or missing dates.

    Args:
        date_str: Raw date value (string, datetime, or NaN).

    Returns:
        Parsed datetime or None if parsing fails.
    """
    if pd.isna(date_str) or date_str is None or str(date_str).strip() == "":
        return None

    if isinstance(date_str, (datetime, date)):
        return datetime.combine(date_str, datetime.min.time()) if isinstance(date_str, date) else date_str

    date_str = str(date_str).strip()

    # Try common date formats
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%b %d, %Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Fallback: try pandas parser
    try:
        return pd.to_datetime(date_str).to_pydatetime()
    except Exception:
        return None


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.

    Args:
        value: Raw value to convert.
        default: Default value if conversion fails.

    Returns:
        Float value or default.
    """
    if pd.isna(value) or value is None:
        return default
    try:
        # Remove commas and currency symbols
        cleaned = re.sub(r"[₹,$,\s]", "", str(value))
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def format_currency(value: float, symbol: str = "₹") -> str:
    """
    Format a numeric value as Indian currency.

    Args:
        value: Numeric value.
        symbol: Currency symbol (default: ₹).

    Returns:
        Formatted currency string.
    """
    if abs(value) >= 1_00_00_000:  # 1 Crore
        return f"{symbol}{value / 1_00_00_000:.2f} Cr"
    elif abs(value) >= 1_00_000:  # 1 Lakh
        return f"{symbol}{value / 1_00_000:.2f} L"
    elif abs(value) >= 1_000:
        return f"{symbol}{value / 1_000:.1f}K"
    else:
        return f"{symbol}{value:,.2f}"


def get_current_quarter() -> tuple[int, int]:
    """
    Get current financial quarter and year.

    Returns:
        Tuple of (quarter_number, year).
    """
    today = datetime.now()
    quarter = (today.month - 1) // 3 + 1
    return quarter, today.year


def is_current_quarter(dt: Optional[datetime]) -> bool:
    """Check if a datetime falls in the current quarter."""
    if dt is None:
        return False
    current_q, current_y = get_current_quarter()
    dt_q = (dt.month - 1) // 3 + 1
    return dt_q == current_q and dt.year == current_y


def is_current_month(dt: Optional[datetime]) -> bool:
    """Check if a datetime falls in the current month."""
    if dt is None:
        return False
    today = datetime.now()
    return dt.month == today.month and dt.year == today.year
