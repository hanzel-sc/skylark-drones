"""
Main Agent Orchestrator.
Coordinates the full BI agent workflow using LangGraph: 
query interpretation → analytical execution → insight generation.
"""

import pandas as pd
from typing import Optional, Any, TypedDict, List
from langgraph.graph import StateGraph, END

from agent.query_interpreter import QueryInterpreter
from agent.insight_generator import InsightGenerator
from data.monday_client import MondayClient
from data.data_cleaning import DataCleaner
from analytics.pipeline_metrics import PipelineMetrics
from analytics.operational_metrics import OperationalMetrics
from analytics.financial_metrics import FinancialMetrics
from config.settings import settings
from utils.logging import get_logger
from utils.helpers import format_currency

logger = get_logger(__name__)


class AgentState(TypedDict):
    """Internal state for the LangGraph BI Agent."""
    query: str
    intent: dict
    result: dict
    insight: str
    warnings: List[str]
    nonsensical: bool
    suggestions: List[str]


class BIAgent:
    """
    Main Business Intelligence Agent.
    Orchestrates the complete workflow using a LangGraph state machine.
    """

    def __init__(self):
        self.interpreter = QueryInterpreter()
        self.insight_gen = InsightGenerator()
        self.monday = MondayClient()
        self.cleaner = DataCleaner()

        # Cached data (persists across queries)
        self._deals_df: Optional[pd.DataFrame] = None
        self._work_orders_df: Optional[pd.DataFrame] = None
        self._data_warnings: List[str] = []

        # Initialize the LangGraph workflow
        self.workflow = self._build_workflow()

    # ------------------------------------------------------------------
    #  Workflow Building (LangGraph)
    # ------------------------------------------------------------------

    def _build_workflow(self):
        """Construct the LangGraph state machine."""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("interpret", self._node_interpret)
        workflow.add_node("execute", self._node_execute)
        workflow.add_node("generate_insight", self._node_generate_insight)

        # Define edges
        workflow.set_entry_point("interpret")
        
        # Conditional edge from interpret
        workflow.add_conditional_edges(
            "interpret",
            self._decide_after_interpretation,
            {
                "execute": "execute",
                "end": END
            }
        )
        
        workflow.add_edge("execute", "generate_insight")
        workflow.add_edge("generate_insight", END)

        return workflow.compile()

    def _node_interpret(self, state: AgentState) -> AgentState:
        """Node to interpret the natural language query."""
        logger.info(f"Node: Interpret | Query: {state['query']}")
        intent = self.interpreter.interpret(state["query"])
        
        new_state = {**state}
        new_state["intent"] = intent
        
        if intent.get("metric") == "nonsensical":
            new_state["nonsensical"] = True
            new_state["suggestions"] = intent.get("suggestions", [])
        else:
            new_state["nonsensical"] = False
            
        return new_state

    def _decide_after_interpretation(self, state: AgentState) -> str:
        """Route to execution or end based on interpretation."""
        if state.get("nonsensical"):
            return "end"
        return "execute"

    def _node_execute(self, state: AgentState) -> AgentState:
        """Node to execute analytical operations."""
        intent = state["intent"]
        metric = intent.get("metric", "general_query")
        sector = intent.get("sector")
        period = intent.get("period")

        logger.info(f"Node: Execute | Metric: {metric}")
        result = self._execute_metric(metric, sector=sector, period=period)
        
        new_state = {**state}
        new_state["result"] = result
        new_state["warnings"] = list(set(state.get("warnings", []) + result.get("warnings", [])))
        return new_state

    def _node_generate_insight(self, state: AgentState) -> AgentState:
        """Node to generate final executive insight."""
        intent = state["intent"]
        metric = intent.get("metric", "general_query")
        result = state["result"]
        
        logger.info("Node: Generate Insight")
        data_summary = self._format_data_summary(metric, result)
        insight = self.insight_gen.generate_insight(state["query"], data_summary)
        
        new_state = {**state}
        new_state["insight"] = insight
        return new_state

    # ------------------------------------------------------------------
    #  Data Loading
    # ------------------------------------------------------------------

    def load_data(
        self,
        deals_board_id: Optional[str] = None,
        work_orders_board_id: Optional[str] = None,
        deals_csv: Optional[str] = None,
        work_orders_csv: Optional[str] = None,
    ) -> dict[str, Any]:
        """Load and clean data from Monday.com boards or CSV fallbacks."""
        self._data_warnings = []
        status = {"deals": "not_loaded", "work_orders": "not_loaded"}

        # --- Load Deals ---
        d_id = deals_board_id or settings.DEALS_BOARD_ID
        if d_id:
            try:
                logger.info(f"Fetching deals from Monday.com board {d_id}")
                raw_deals = self.monday.fetch_board_as_dataframe(d_id)
                self._deals_df = self.cleaner.clean_deals(raw_deals)
                self._data_warnings.extend(self.cleaner.get_warnings())
                status["deals"] = "loaded_from_api"
            except Exception as e:
                logger.error(f"Failed to fetch deals from API: {e}")
                self._data_warnings.append(
                    "Unable to retrieve latest data from Monday.com. Using CSV fallback."
                )
                if deals_csv:
                    self._load_deals_csv(deals_csv)
                    status["deals"] = "loaded_from_csv"
        elif deals_csv:
            self._load_deals_csv(deals_csv)
            status["deals"] = "loaded_from_csv"

        # --- Load Work Orders ---
        wo_id = work_orders_board_id or settings.WORK_ORDERS_BOARD_ID
        if wo_id:
            try:
                logger.info(f"Fetching work orders from Monday.com board {wo_id}")
                raw_wo = self.monday.fetch_board_as_dataframe(wo_id)
                self._work_orders_df = self.cleaner.clean_work_orders(raw_wo)
                self._data_warnings.extend(self.cleaner.get_warnings())
                status["work_orders"] = "loaded_from_api"
            except Exception as e:
                logger.error(f"Failed to fetch work orders from API: {e}")
                self._data_warnings.append("Unable to retrieve work order data from Monday.com.")
                if work_orders_csv:
                    self._load_work_orders_csv(work_orders_csv)
                    status["work_orders"] = "loaded_from_csv"
        elif work_orders_csv:
            self._load_work_orders_csv(work_orders_csv)
            status["work_orders"] = "loaded_from_csv"

        status["warnings"] = self._data_warnings
        return status

    def _load_deals_csv(self, path: str) -> None:
        try:
            raw = pd.read_csv(path)
            self._deals_df = self.cleaner.clean_deals(raw)
            self._data_warnings.extend(self.cleaner.get_warnings())
        except Exception as e:
            logger.error(f"Failed to load deals CSV: {e}")
            self._data_warnings.append(f"Failed to load deals data: {e}")

    def _load_work_orders_csv(self, path: str) -> None:
        try:
            raw = pd.read_csv(path, header=1)
            self._work_orders_df = self.cleaner.clean_work_orders(raw)
            self._data_warnings.extend(self.cleaner.get_warnings())
        except Exception as e:
            logger.error(f"Failed to load work orders CSV: {e}")
            self._data_warnings.append(f"Failed to load work orders data: {e}")

    # ------------------------------------------------------------------
    #  Query Processing
    # ------------------------------------------------------------------

    def process_query(self, user_query: str) -> dict[str, Any]:
        """Process a query end-to-end using the LangGraph workflow."""
        logger.info(f"Processing query via LangGraph: {user_query}")
        
        initial_state: AgentState = {
            "query": user_query,
            "intent": {},
            "result": {},
            "insight": "",
            "warnings": self._data_warnings.copy(),
            "nonsensical": False,
            "suggestions": []
        }
        
        final_state = self.workflow.invoke(initial_state)
        
        result = final_state.get("result", {})
        
        return {
            "intent": final_state.get("intent", {}),
            "insight": final_state.get("insight", ""),
            "nonsensical": final_state.get("nonsensical", False),
            "suggestions": final_state.get("suggestions", []),
            "data": result.get("data"),
            "chart_data": result.get("chart_data"),
            "chart_type": result.get("chart_type"),
            "kpis": result.get("kpis"),
            "warnings": final_state.get("warnings", []),
        }

    def _execute_metric(self, metric: str, sector: Optional[str] = None, period: Optional[str] = None) -> dict[str, Any]:
        """Execute analytics functions based on metric name."""
        res: dict[str, Any] = {"data": None, "chart_data": None, "chart_type": None, "kpis": None, "warnings": []}

        if self._deals_df is None and metric not in [
            "work_orders_by_sector", "execution_status", "billing_completion_rate",
            "total_billed", "total_collected", "receivables", "billing_vs_collection",
            "financial_summary",
        ]:
            res["warnings"].append("Deals data not loaded.")
            return res

        try:
            if metric == "pipeline_value" or metric == "pipeline_by_sector":
                pm = PipelineMetrics(self._deals_df)
                data = pm.pipeline_value_by_sector()
                res.update({"data": data, "chart_data": data, "chart_type": "bar_sector", "kpis": {"total_pipeline": pm.total_pipeline_value()}})
                pm.close()
            elif metric == "pipeline_by_stage":
                pm = PipelineMetrics(self._deals_df)
                data = pm.pipeline_by_stage()
                res.update({"data": data, "chart_data": data, "chart_type": "bar_stage"})
                pm.close()
            elif metric == "deals_closing_soon":
                pm = PipelineMetrics(self._deals_df)
                data = pm.deals_closing_this_month() if period == "current_month" else pm.deals_closing_this_quarter(sector=sector)
                res.update({"data": data, "chart_type": "table"})
                pm.close()
            elif metric == "average_deal_size":
                pm = PipelineMetrics(self._deals_df)
                res["kpis"] = {"average_deal_size": pm.average_deal_size()}
                pm.close()
            elif metric == "active_deals":
                pm = PipelineMetrics(self._deals_df)
                res["kpis"] = {"active_deals": pm.active_deals_count()}
                pm.close()
            elif metric == "deal_trends":
                pm = PipelineMetrics(self._deals_df)
                data = pm.deal_creation_trend()
                res.update({"data": data, "chart_data": data, "chart_type": "line_trend"})
                pm.close()
            elif metric == "work_orders_by_sector":
                if self._work_orders_df is not None:
                    om = OperationalMetrics(self._work_orders_df)
                    data = om.work_orders_by_sector()
                    res.update({"data": data, "chart_data": data, "chart_type": "bar_sector"})
                    om.close()
                else:
                    res["warnings"].append("Work orders data not loaded.")
            elif metric == "execution_status":
                if self._work_orders_df is not None:
                    om = OperationalMetrics(self._work_orders_df)
                    data = om.execution_status_distribution()
                    res.update({"data": data, "chart_data": data, "chart_type": "pie"})
                    om.close()
                else:
                    res["warnings"].append("Work orders data not loaded.")
            elif metric == "billing_completion_rate":
                if self._work_orders_df is not None:
                    om = OperationalMetrics(self._work_orders_df)
                    res["kpis"] = om.billing_completion_rate()
                    om.close()
                else:
                    res["warnings"].append("Work orders data not loaded.")
            elif metric == "total_billed":
                if self._work_orders_df is not None:
                    fm = FinancialMetrics(self._work_orders_df)
                    res["kpis"] = {"total_billed": fm.total_billed()}
                    fm.close()
            elif metric == "total_collected":
                if self._work_orders_df is not None:
                    fm = FinancialMetrics(self._work_orders_df)
                    res["kpis"] = {"total_collected": fm.total_collected()}
                    fm.close()
            elif metric == "receivables":
                if self._work_orders_df is not None:
                    fm = FinancialMetrics(self._work_orders_df)
                    by_sector = fm.receivables_by_sector()
                    res.update({"kpis": {"total_receivable": fm.receivable_amount()}, "data": by_sector, "chart_data": by_sector, "chart_type": "bar_sector"})
                    fm.close()
            elif metric == "billing_vs_collection":
                if self._work_orders_df is not None:
                    fm = FinancialMetrics(self._work_orders_df)
                    data = fm.billing_vs_collection()
                    res.update({"data": data, "chart_data": data, "chart_type": "grouped_bar"})
                    fm.close()
            elif metric == "financial_summary":
                if self._work_orders_df is not None:
                    fm = FinancialMetrics(self._work_orders_df)
                    res["kpis"] = fm.financial_summary()
                    fm.close()
            elif metric == "leadership_update":
                res = self._generate_leadership_data()
            else:
                res["data"] = self._build_context_summary()
                res["chart_type"] = "none"
        except Exception as e:
            logger.error(f"Error executing metric '{metric}': {e}")
            res["warnings"].append(f"Error computing analytics: {str(e)}")
        return res

    def generate_leadership_update(self) -> str:
        """Generate a comprehensive leadership update."""
        data = self._generate_leadership_data()
        summary = self._format_data_summary("leadership_update", data)
        return self.insight_gen.generate_leadership_update(summary)

    def _generate_leadership_data(self) -> dict[str, Any]:
        result: dict[str, Any] = {"data": None, "chart_data": None, "chart_type": "none", "kpis": {}, "warnings": []}
        if self._deals_df is not None:
            try:
                pm = PipelineMetrics(self._deals_df)
                result["kpis"].update({"total_pipeline": pm.total_pipeline_value(), "active_deals": pm.active_deals_count(), "avg_deal_size": pm.average_deal_size()})
                sector_data = pm.pipeline_value_by_sector()
                if not sector_data.empty:
                    result["kpis"].update({"top_sector": sector_data.iloc[0]["sector"], "top_sector_value": sector_data.iloc[0]["total_value"]})
                neg_deals = self._deals_df[(self._deals_df["deal_stage"] == "F. Negotiations") & (self._deals_df["deal_status"] == "Open")]
                result["kpis"]["deals_in_negotiation"] = len(neg_deals)
                pm.close()
            except Exception as e:
                result["warnings"].append(f"Error computing pipeline metrics: {e}")
        if self._work_orders_df is not None:
            try:
                om = OperationalMetrics(self._work_orders_df)
                result["kpis"]["active_work_orders"] = om.active_work_orders()
                result["kpis"]["billing_completion"] = om.billing_completion_rate()["completion_rate"]
                om.close()
                fm = FinancialMetrics(self._work_orders_df)
                result["kpis"].update({"total_receivable": fm.receivable_amount(), "total_billed": fm.total_billed(), "total_collected": fm.total_collected(), "collection_rate": fm.collection_rate()})
                fm.close()
            except Exception as e:
                result["warnings"].append(f"Error computing operational metrics: {e}")
        return result

    def _format_data_summary(self, metric: str, result: dict) -> str:
        parts = []
        if result.get("kpis"):
            parts.append("Key Metrics:")
            for k, v in result["kpis"].items():
                parts.append(f"  - {k}: {format_currency(v) if isinstance(v, float) and v > 1000 else v}")
        if isinstance(result.get("data"), pd.DataFrame) and not result["data"].empty:
            parts.append(f"\nData Breakdown:\n{result['data'].to_string(index=False, max_rows=20)}")
        if result.get("warnings"):
            parts.append("\nData Quality Notes:")
            for w in result["warnings"]:
                parts.append(f"  ⚠️ {w}")
        return "\n".join(parts) if parts else "No data available."

    def _build_context_summary(self) -> str:
        parts = []
        if self._deals_df is not None:
            parts.append(f"Deals dataset: {len(self._deals_df)} records")
            if "sector" in self._deals_df.columns:
                parts.append(f"Top sectors: {dict(self._deals_df['sector'].value_counts().head(5))}")
            if "deal_status" in self._deals_df.columns:
                parts.append(f"Status distribution: {dict(self._deals_df['deal_status'].value_counts())}")
        if self._work_orders_df is not None:
            parts.append(f"Work orders dataset: {len(self._work_orders_df)} records")
        return "\n".join(parts)

    def get_deals_df(self) -> Optional[pd.DataFrame]: return self._deals_df
    def get_work_orders_df(self) -> Optional[pd.DataFrame]: return self._work_orders_df
