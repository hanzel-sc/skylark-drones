"""
Configuration settings for Monday BI Agent.
Manages environment variables and application-wide constants.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Auto-load .env file from project root
load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # --- API Keys ---
    MONDAY_API_KEY: str = field(
        default_factory=lambda: os.getenv(
            "MONDAY_API_KEY", ""
        )
    )
    GROQ_API_KEY: str = field(
        default_factory=lambda: os.getenv(
            "GROQ_API_KEY", ""
        )
    )

    # --- Monday.com API ---
    MONDAY_API_URL: str = "https://api.monday.com/v2"
    MONDAY_API_VERSION: str = "2024-10"

    # --- Board IDs (to be configured per deployment) ---
    DEALS_BOARD_ID: Optional[str] = field(
        default_factory=lambda: os.getenv("DEALS_BOARD_ID", None)
    )
    WORK_ORDERS_BOARD_ID: Optional[str] = field(
        default_factory=lambda: os.getenv("WORK_ORDERS_BOARD_ID", None)
    )

    # --- LLM Settings ---
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096

    # --- Application ---
    APP_TITLE: str = "Monday BI Agent"
    APP_SUBTITLE: str = "AI-Powered Business Intelligence for Founders"
    LOG_LEVEL: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )

    # --- Data Quality ---
    DEFAULT_NUMERIC_FILL: float = 0.0
    DEFAULT_CATEGORICAL_FILL: str = "unknown"

    # --- Sector Normalization Map ---
    SECTOR_ALIASES: dict = field(default_factory=lambda: {
        "energy": "energy",
        "energy sector": "energy",
        "mining": "mining",
        "mining sector": "mining",
        "renewables": "renewables",
        "renewable": "renewables",
        "renewable energy": "renewables",
        "powerline": "powerline",
        "power line": "powerline",
        "railways": "railways",
        "railway": "railways",
        "rail": "railways",
        "construction": "construction",
        "dsp": "dsp",
        "tender": "tender",
        "others": "others",
        "other": "others",
        "security and surveillance": "security_and_surveillance",
        "manufacturing": "manufacturing",
        "aviation": "aviation",
    })

    # --- Deal Stage Normalization ---
    DEAL_STAGE_ORDER: list = field(default_factory=lambda: [
        "A. Lead Generated",
        "B. Sales Qualified Leads",
        "C. Demo Done",
        "D. Feasibility",
        "E. Proposal/Commercials Sent",
        "F. Negotiations",
        "G. Project Won",
        "H. Work Order Received",
        "I. POC",
        "J. Invoice sent",
        "K. Amount Accrued",
        "L. Project Lost",
        "M. Projects On Hold",
        "N. Not relevant at the moment",
        "O. Not Relevant at all",
        "Project Completed",
    ])


# Singleton instance
settings = Settings()
