"""
Query Interpreter Module.
Uses Groq LLM (Llama 3.1) to interpret natural language business questions
into structured analytical intents. Handles edge cases for nonsensical input.
"""

import json
import re
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import settings
from utils.logging import get_logger

logger = get_logger(__name__)

# System prompt for the query interpreter
INTERPRETER_SYSTEM_PROMPT = """You are a business intelligence query interpreter for a drone services company (Skylark).

Your job is to interpret natural language business questions and extract structured intent.

Available metrics:
- pipeline_value: Total value of deals in pipeline
- pipeline_by_sector: Pipeline breakdown by sector
- pipeline_by_stage: Pipeline breakdown by deal stage
- deals_closing_soon: Deals expected to close this month/quarter
- average_deal_size: Average size of deals
- active_deals: Count of active deals
- deal_trends: Deal creation trends over time
- work_orders_by_sector: Work order distribution by sector
- execution_status: Work order execution status distribution
- billing_completion_rate: Percentage of work orders billed
- total_billed: Total billed amount
- total_collected: Total collected amount
- receivables: Outstanding receivable amounts
- billing_vs_collection: Comparison of billing and collection
- financial_summary: Overall financial health summary
- leadership_update: Executive summary of all key metrics

Available sectors: mining, renewables, powerline, railways, construction, dsp, tender, others, security_and_surveillance, manufacturing, aviation

Available time periods: current_month, current_quarter, all_time

IMPORTANT: If the user's input is gibberish, random characters, completely unrelated to business
(e.g. "asdfghjkl", "hello how are you", "tell me a joke", "what is the weather"),
or cannot be mapped to any metric, set metric to "nonsensical" and provide a helpful description.

Respond ONLY with a JSON object containing:
{
    "metric": "<metric_name>",
    "sector": "<sector_name or null>",
    "period": "<time_period or null>",
    "status_filter": "<deal_status or null>",
    "description": "<brief description of what the user is asking>"
}
"""

# Suggested queries shown when user input is nonsensical
SUGGESTED_QUERIES = [
    "How is our pipeline looking for the mining sector this quarter?",
    "What deals are likely to close this month?",
    "Which sectors generate the most revenue?",
    "How much receivable revenue do we have?",
    "What is the billing completion rate?",
    "Show me pipeline by deal stage",
    "Give me a leadership update",
]

# Minimum viable query length
MIN_QUERY_LENGTH = 3

# Patterns that indicate gibberish
GIBBERISH_PATTERNS = [
    r'^[^a-zA-Z]*$',                    # No letters at all
    r'^(.)\1{4,}$',                      # Repeated single character 5+ times
    r'^[a-z]{1,2}$',                     # Single/double letter
    r'^[^aeiouAEIOU\s]{6,}$',           # 6+ consonants with no vowels
]


class QueryInterpreter:
    """Interprets natural language queries into structured analytical intents."""

    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=1024,
        )

    def interpret(self, user_query: str) -> dict:
        """
        Interpret a natural language business question.

        Args:
            user_query: The user's question in natural language.

        Returns:
            Structured dict with metric, sector, period, and description.
        """
        logger.info(f"Interpreting query: {user_query}")

        # --- Pre-validation: catch obvious nonsense before hitting the LLM ---
        cleaned = user_query.strip()
        if not cleaned or len(cleaned) < MIN_QUERY_LENGTH:
            logger.info("Query too short, flagging as nonsensical")
            return self._nonsensical_result(cleaned)

        if self._is_gibberish(cleaned):
            logger.info("Query detected as gibberish")
            return self._nonsensical_result(cleaned)

        # --- LLM interpretation ---
        messages = [
            SystemMessage(content=INTERPRETER_SYSTEM_PROMPT),
            HumanMessage(content=user_query),
        ]

        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()

            parsed = self._extract_json(content)
            logger.info(f"Interpreted intent: {parsed}")

            # If the LLM flagged it as nonsensical
            if parsed.get("metric") == "nonsensical":
                return self._nonsensical_result(cleaned)

            return parsed

        except Exception as e:
            logger.error(f"Query interpretation failed: {e}")
            return {
                "metric": "general_query",
                "sector": None,
                "period": None,
                "status_filter": None,
                "description": user_query,
            }

    def _is_gibberish(self, text: str) -> bool:
        """
        Detect if input is likely gibberish.

        Args:
            text: Cleaned user input.

        Returns:
            True if the input appears to be gibberish.
        """
        for pattern in GIBBERISH_PATTERNS:
            if re.match(pattern, text):
                return True
        return False

    def _nonsensical_result(self, original_query: str) -> dict:
        """
        Build a structured response for nonsensical queries.

        Args:
            original_query: The original user input.

        Returns:
            Intent dict with metric="nonsensical" and suggestions.
        """
        return {
            "metric": "nonsensical",
            "sector": None,
            "period": None,
            "status_filter": None,
            "description": original_query,
            "suggestions": SUGGESTED_QUERIES,
        }

    def _extract_json(self, text: str) -> dict:
        """
        Extract JSON from LLM response text, handling markdown code blocks.

        Args:
            text: Raw LLM response.

        Returns:
            Parsed JSON dict.
        """
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        if "```" in text:
            code_block = text.split("```")[1]
            if code_block.startswith("json"):
                code_block = code_block[4:]
            try:
                return json.loads(code_block.strip())
            except json.JSONDecodeError:
                pass

        # Try to find JSON-like content
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # Fallback
        logger.warning(f"Could not parse JSON from LLM response: {text[:200]}")
        return {
            "metric": "general_query",
            "sector": None,
            "period": None,
            "status_filter": None,
            "description": text,
        }
