"""
Monday.com GraphQL API Client.
Fetches board data dynamically with pagination and error handling.
"""

import requests
import pandas as pd
from typing import Optional

from config.settings import settings
from utils.logging import get_logger

logger = get_logger(__name__)


class MondayClient:
    """Client for interacting with the Monday.com GraphQL API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.MONDAY_API_KEY
        self.api_url = settings.MONDAY_API_URL
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "API-Version": settings.MONDAY_API_VERSION,
        }

    def _execute_query(self, query: str, variables: Optional[dict] = None) -> dict:
        """
        Execute a GraphQL query against the Monday.com API.

        Args:
            query: GraphQL query string.
            variables: Optional query variables.

        Returns:
            Parsed JSON response.

        Raises:
            ConnectionError: If the API is unreachable.
            ValueError: If the response contains errors.
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                error_msgs = [e.get("message", "Unknown error") for e in data["errors"]]
                logger.error(f"Monday.com API errors: {error_msgs}")
                raise ValueError(f"Monday.com API errors: {'; '.join(error_msgs)}")

            return data

        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Monday.com API")
            raise ConnectionError("Unable to retrieve latest data from Monday.com. Please check your network connection.")
        except requests.exceptions.Timeout:
            logger.error("Monday.com API request timed out")
            raise ConnectionError("Monday.com API request timed out. Please try again.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error from Monday.com API: {e}")
            raise ConnectionError(f"Monday.com API returned an error: {e}")

    def get_boards(self) -> list[dict]:
        """Fetch list of all accessible boards."""
        query = """
        query {
            boards(limit: 50) {
                id
                name
                columns {
                    id
                    title
                    type
                }
            }
        }
        """
        result = self._execute_query(query)
        boards = result.get("data", {}).get("boards", [])
        logger.info(f"Fetched {len(boards)} boards from Monday.com")
        return boards

    def get_board_items(
        self,
        board_id: str,
        limit: int = 500,
        cursor: Optional[str] = None,
    ) -> tuple[list[dict], Optional[str]]:
        """
        Fetch items from a specific board with pagination.

        Args:
            board_id: The Monday.com board ID.
            limit: Number of items per page (max 500).
            cursor: Pagination cursor for next page.

        Returns:
            Tuple of (items list, next cursor or None).
        """
        if cursor:
            query = """
            query ($cursor: String!) {
                next_items_page(cursor: $cursor, limit: %d) {
                    cursor
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                            value
                            type
                            column {
                                title
                            }
                        }
                    }
                }
            }
            """ % limit
            variables = {"cursor": cursor}
            result = self._execute_query(query, variables)
            page_data = result.get("data", {}).get("next_items_page", {})
        else:
            query = """
            query ($boardId: [ID!]!) {
                boards(ids: $boardId) {
                    items_page(limit: %d) {
                        cursor
                        items {
                            id
                            name
                            column_values {
                                id
                                text
                                value
                                type
                                column {
                                    title
                                }
                            }
                        }
                    }
                }
            }
            """ % limit
            variables = {"boardId": [board_id]}
            result = self._execute_query(query, variables)
            boards = result.get("data", {}).get("boards", [])
            if not boards:
                logger.warning(f"No board found with ID: {board_id}")
                return [], None
            page_data = boards[0].get("items_page", {})

        items = page_data.get("items", [])
        next_cursor = page_data.get("cursor")
        logger.info(f"Fetched {len(items)} items from board {board_id}")
        return items, next_cursor

    def fetch_all_board_items(self, board_id: str) -> list[dict]:
        """
        Fetch ALL items from a board, handling pagination automatically.

        Args:
            board_id: The Monday.com board ID.

        Returns:
            Complete list of all items.
        """
        all_items = []
        cursor = None
        page = 0

        while True:
            page += 1
            items, cursor = self.get_board_items(board_id, limit=500, cursor=cursor)
            all_items.extend(items)
            logger.info(f"Page {page}: fetched {len(items)} items (total: {len(all_items)})")

            if not cursor or not items:
                break

        logger.info(f"Total items fetched from board {board_id}: {len(all_items)}")
        return all_items

    def items_to_dataframe(self, items: list[dict]) -> pd.DataFrame:
        """
        Convert Monday.com items to a pandas DataFrame.

        Args:
            items: List of item dicts from the API.

        Returns:
            DataFrame with item names and column values.
        """
        rows = []
        for item in items:
            row = {"item_id": item.get("id"), "item_name": item.get("name", "")}
            for col in item.get("column_values", []):
                # API v2024-10: title is nested under column { title }
                col_obj = col.get("column", {})
                col_title = col_obj.get("title") if col_obj else col.get("id", "unknown")
                col_text = col.get("text", "")
                row[col_title] = col_text
            rows.append(row)

        df = pd.DataFrame(rows)
        logger.info(f"Converted {len(rows)} items to DataFrame with {len(df.columns)} columns")
        return df

    def fetch_board_as_dataframe(self, board_id: str) -> pd.DataFrame:
        """
        High-level method: fetch all items from a board and return as DataFrame.

        Args:
            board_id: The Monday.com board ID.

        Returns:
            Cleaned DataFrame of board data.
        """
        items = self.fetch_all_board_items(board_id)
        return self.items_to_dataframe(items)

    def find_board_by_name(self, name_substring: str) -> Optional[dict]:
        """
        Find a board by matching a substring of its name.

        Args:
            name_substring: Partial name to search for.

        Returns:
            Board dict if found, None otherwise.
        """
        boards = self.get_boards()
        name_lower = name_substring.lower()
        for board in boards:
            if name_lower in board.get("name", "").lower():
                logger.info(f"Found board: {board['name']} (ID: {board['id']})")
                return board
        logger.warning(f"No board found matching '{name_substring}'")
        return None
