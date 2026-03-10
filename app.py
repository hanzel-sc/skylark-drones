"""
Monday BI Agent — Streamlit Dashboard Application.
AI-Powered Business Intelligence for Founders.
"""

import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.agent import BIAgent
from utils.helpers import format_currency
from utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# Page Config
# =============================================================================
st.set_page_config(
    page_title="Monday BI Agent",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# Color Palette
#   Background:  #0B0C10
#   Surface:     #1F2833
#   Muted Text:  #C5C6C7
#   Accent:      #66FCF1
#   Accent Alt:  #45A29E
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Reset & Base ── */
    *, *::before, *::after { box-sizing: border-box; }
    .stApp {
        background: #0B0C10;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #C5C6C7;
    }
    .main .block-container {
        padding: 1.5rem 2rem;
        max-width: 1440px;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #0B0C10; }
    ::-webkit-scrollbar-thumb { background: #1F2833; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #45A29E; }

    /* ── Header Bar ── */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.5rem;
        background: #1F2833;
        border: 1px solid rgba(102, 252, 241, 0.08);
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .app-header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .app-logo {
        width: 34px; height: 34px;
        background: linear-gradient(135deg, #66FCF1 0%, #45A29E 100%);
        border-radius: 7px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 15px; color: #0B0C10;
    }
    .app-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #FAFAFA;
        letter-spacing: -0.02em;
    }
    .app-subtitle {
        font-size: 0.75rem;
        color: #C5C6C7;
        font-weight: 400;
        margin-top: 1px;
        letter-spacing: 0.01em;
    }
    .app-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        background: rgba(102, 252, 241, 0.06);
        border: 1px solid rgba(102, 252, 241, 0.15);
        font-size: 0.7rem;
        font-weight: 500;
        color: #66FCF1;
        letter-spacing: 0.02em;
    }
    .app-badge-dot {
        width: 5px; height: 5px;
        background: #66FCF1;
        border-radius: 50%;
        animation: pulse-dot 2s ease-in-out infinite;
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    /* ── KPI Cards ── */
    .kpi-card {
        background: #1F2833;
        border: 1px solid rgba(102, 252, 241, 0.07);
        border-radius: 10px;
        padding: 1.15rem 1.35rem;
        transition: border-color 0.2s ease;
    }
    .kpi-card:hover {
        border-color: rgba(102, 252, 241, 0.2);
    }
    .kpi-label {
        font-size: 0.7rem;
        font-weight: 500;
        color: #C5C6C7;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #66FCF1;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.68rem;
        color: #45A29E;
        margin-top: 5px;
        font-weight: 400;
    }

    /* ── Section Headers ── */
    .section-header {
        font-size: 0.82rem;
        font-weight: 600;
        color: #FAFAFA;
        letter-spacing: -0.01em;
        margin-bottom: 0.85rem;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid rgba(102, 252, 241, 0.07);
    }

    /* ── Chat ── */
    .stChatInput > div { border-color: #1F2833 !important; }
    .stChatInput input {
        background: #1F2833 !important;
        color: #FAFAFA !important;
        border: 1px solid rgba(102, 252, 241, 0.1) !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.88rem !important;
    }
    .stChatInput input::placeholder { color: #45A29E !important; }
    .stChatMessage {
        background: transparent !important;
        border: none !important;
    }

    /* ── Insight Card ── */
    .insight-card {
        background: #1F2833;
        border: 1px solid rgba(102, 252, 241, 0.08);
        border-radius: 10px;
        padding: 1.15rem 1.4rem;
        margin: 0.6rem 0;
        font-size: 0.86rem;
        line-height: 1.7;
        color: #C5C6C7;
    }
    .insight-card strong, .insight-card b { color: #FAFAFA; }
    .insight-card h2, .insight-card h3 { color: #66FCF1; font-weight: 600; }

    /* ── Nonsensical / Rephrase ── */
    .rephrase-card {
        background: #1F2833;
        border: 1px solid rgba(102, 252, 241, 0.1);
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin: 0.6rem 0;
    }
    .rephrase-title {
        font-size: 0.88rem;
        font-weight: 600;
        color: #FAFAFA;
        margin-bottom: 0.6rem;
    }
    .rephrase-msg {
        font-size: 0.82rem;
        color: #C5C6C7;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    .rephrase-suggestion {
        display: block;
        padding: 8px 14px;
        margin-bottom: 6px;
        border-radius: 6px;
        background: rgba(102, 252, 241, 0.04);
        border: 1px solid rgba(102, 252, 241, 0.08);
        font-size: 0.78rem;
        color: #66FCF1;
        cursor: pointer;
        transition: background 0.15s;
    }
    .rephrase-suggestion:hover {
        background: rgba(102, 252, 241, 0.1);
    }

    /* ── Warning ── */
    .warning-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 6px;
        background: rgba(250, 204, 21, 0.06);
        border: 1px solid rgba(250, 204, 21, 0.12);
        font-size: 0.75rem;
        color: #facc15;
        margin: 3px 0;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0B0C10;
        border-right: 1px solid rgba(102, 252, 241, 0.06);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #C5C6C7; }
    [data-testid="stSidebar"] .stRadio label { color: #C5C6C7 !important; font-size: 0.82rem !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FAFAFA !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: #1F2833 !important;
        color: #C5C6C7 !important;
        border: 1px solid rgba(102, 252, 241, 0.1) !important;
        border-radius: 7px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        padding: 7px 14px !important;
        transition: all 0.15s ease !important;
        letter-spacing: 0.01em !important;
    }
    .stButton > button:hover {
        background: rgba(102, 252, 241, 0.06) !important;
        color: #66FCF1 !important;
        border-color: rgba(102, 252, 241, 0.2) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #45A29E 0%, #66FCF1 100%) !important;
        color: #0B0C10 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        opacity: 0.9 !important;
    }

    /* ── Download button ── */
    .stDownloadButton > button {
        background: #1F2833 !important;
        color: #66FCF1 !important;
        border: 1px solid rgba(102, 252, 241, 0.15) !important;
        border-radius: 7px !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.78rem !important;
    }

    /* ── Plotly ── */
    .js-plotly-plot .plotly .modebar { display: none !important; }

    /* ── Dataframes ── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* ── Footer ── */
    .app-footer {
        text-align: center;
        padding: 2rem 0 1rem;
        color: #45A29E;
        font-size: 0.68rem;
        letter-spacing: 0.03em;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: #0B0C10; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# Session State
# =============================================================================
if "agent" not in st.session_state:
    st.session_state.agent = BIAgent()
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "load_status" not in st.session_state:
    st.session_state.load_status = None


# =============================================================================
# Helpers
# =============================================================================

def render_kpi_card(label: str, value: str, sub: str = ""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def plotly_layout(fig, title: str = ""):
    """Apply the #0B0C10 / #66FCF1 themed dark layout to Plotly charts."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#FAFAFA", family="Inter"),
                   x=0, xanchor="left", pad=dict(b=12)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#C5C6C7", size=11, family="Inter"),
        showlegend=False,
        margin=dict(l=45, r=15, t=50, b=45),
        xaxis=dict(
            gridcolor="rgba(102,252,241,0.04)",
            zerolinecolor="rgba(102,252,241,0.06)",
            tickfont=dict(size=10, color="#C5C6C7"),
        ),
        yaxis=dict(
            gridcolor="rgba(102,252,241,0.04)",
            zerolinecolor="rgba(102,252,241,0.06)",
            tickfont=dict(size=10, color="#C5C6C7"),
        ),
    )
    return fig


# Vibrant diverse chart color palette
CHART_COLORS = [
    "#66FCF1", "#FF007F", "#7C3AED", "#FFBF00", "#00FF7F",
    "#45A29E", "#FF5F1F", "#A78BFA", "#C5C6C7", "#32CD32",
]


def render_chart(chart_data: pd.DataFrame, chart_type: str):
    """Render Plotly chart with consistent premium styling."""
    if chart_data is None or chart_data.empty:
        return

    if chart_type == "bar_sector":
        value_col = "total_value" if "total_value" in chart_data.columns else "receivable_amount"
        # Use sector for color to make it diverse
        fig = px.bar(chart_data, x="sector", y=value_col, color="sector",
                     color_discrete_sequence=CHART_COLORS)
        fig = plotly_layout(fig, "Breakdown by Sector")
        fig.update_traces(
            marker_line_width=0,
            marker_color="#66FCF1",
            marker_opacity=0.85,
            hovertemplate="<b>%{x}</b><br>Value: %{y:,.0f}<extra></extra>",
        )
        fig.update_layout(
            xaxis_title=None, yaxis_title=None,
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "bar_stage":
        fig = px.bar(chart_data, x="deal_stage", y="total_value", color="deal_stage",
                     color_discrete_sequence=CHART_COLORS)
        fig = plotly_layout(fig, "Pipeline by Deal Stage")
        fig.update_traces(
            marker_line_width=0,
            marker_color="#45A29E",
            marker_opacity=0.85,
            hovertemplate="<b>%{x}</b><br>Value: %{y:,.0f}<extra></extra>",
        )
        fig.update_layout(
            xaxis_title=None, yaxis_title=None,
            xaxis_tickangle=-35,
        )
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "pie":
        count_col = "count" if "count" in chart_data.columns else chart_data.columns[-1]
        name_col = chart_data.columns[0]
        fig = px.pie(chart_data, values=count_col, names=name_col,
                     color_discrete_sequence=CHART_COLORS, hole=0.55)
        fig = plotly_layout(fig, "Distribution")
        fig.update_traces(
            textfont_size=10, textfont_color="#C5C6C7",
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
            marker_line_width=1, marker_line_color="#0B0C10",
        )
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "line_trend":
        fig = px.line(chart_data, x="month", y="deal_count", markers=True)
        fig = plotly_layout(fig, "Deal Creation Trend")
        fig.update_traces(
            line_color="#66FCF1", line_width=2.5,
            marker=dict(size=7, color="#0B0C10", line=dict(width=2, color="#66FCF1")),
            hovertemplate="<b>%{x}</b><br>Deals: %{y}<extra></extra>",
        )
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "grouped_bar":
        fig = go.Figure()
        bar_map = {
            "billed": ("#66FCF1", "Billed"),
            "collected": ("#45A29E", "Collected"),
            "receivable": ("#C5C6C7", "Receivable"),
        }
        for col, (color, name) in bar_map.items():
            if col in chart_data.columns:
                fig.add_trace(go.Bar(
                    name=name, x=chart_data["sector"], y=chart_data[col],
                    marker_color=color, marker_line_width=0, marker_opacity=0.85,
                    hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:,.0f}}<extra></extra>",
                ))
        fig.update_layout(barmode="group")
        fig = plotly_layout(fig, "Billing vs Collection")
        fig.update_layout(
            showlegend=True,
            legend=dict(font=dict(size=10, color="#C5C6C7"),
                        bgcolor="rgba(0,0,0,0)", borderwidth=0,
                        orientation="h", yanchor="bottom", y=1.02,
                        xanchor="left", x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "table":
        st.dataframe(chart_data, use_container_width=True)


# =============================================================================
# Sidebar
# =============================================================================
with st.sidebar:
    st.markdown("### Configuration")

    data_source = st.radio(
        "Data Source",
        ["Monday.com API", "CSV Files (Fallback)"],
        index=1,
    )

    if data_source == "Monday.com API":
        deals_board_id = st.text_input("Deals Board ID",
                                       value=os.getenv("DEALS_BOARD_ID", ""))
        wo_board_id = st.text_input("Work Orders Board ID",
                                    value=os.getenv("WORK_ORDERS_BOARD_ID", ""))
    else:
        deals_board_id = None
        wo_board_id = None

    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)

    deals_csv = next(
        (p for p in [os.path.join(parent_dir, "Deal_funnel_Data.csv"),
                     os.path.join(base_dir, "Deal_funnel_Data.csv")]
         if os.path.exists(p)), None)
    wo_csv = next(
        (p for p in [os.path.join(parent_dir, "Work_Order_Tracker_Data.csv"),
                     os.path.join(base_dir, "Work_Order_Tracker_Data.csv")]
         if os.path.exists(p)), None)

    if st.button("Load / Refresh Data", type="primary", use_container_width=True):
        with st.spinner("Loading data..."):
            status = st.session_state.agent.load_data(
                deals_board_id=deals_board_id,
                work_orders_board_id=wo_board_id,
                deals_csv=deals_csv,
                work_orders_csv=wo_csv,
            )
            st.session_state.data_loaded = True
            st.session_state.load_status = status
        if status.get("warnings"):
            for w in status["warnings"]:
                st.warning(w)
        st.success(f"Deals: {status.get('deals')} | Work Orders: {status.get('work_orders')}")

    st.markdown("---")
    st.markdown("### Example Queries")
    examples = [
        "How is our pipeline looking for mining this quarter?",
        "What deals are likely to close this month?",
        "Which sectors generate the most revenue?",
        "How much receivable revenue do we have?",
        "What is the billing completion rate?",
        "Show pipeline by deal stage",
        "Deal creation trend",
        "Work orders by sector",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{hash(ex)}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": ex})
            st.rerun()

# =============================================================================
# Header
# =============================================================================
st.markdown("""
<div class="app-header">
    <div class="app-header-left">
        <div class="app-logo">M</div>
        <div>
            <div class="app-title">Monday BI Agent</div>
            <div class="app-subtitle">Business Intelligence for Founders</div>
        </div>
    </div>
    <div class="app-badge">
        <span class="app-badge-dot"></span>
        Llama 3.1 via Groq
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# KPI Row
# =============================================================================
if st.session_state.data_loaded:
    agent = st.session_state.agent
    deals_df = agent.get_deals_df()
    wo_df = agent.get_work_orders_df()

    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        if deals_df is not None:
            from analytics.pipeline_metrics import PipelineMetrics
            pm = PipelineMetrics(deals_df)
            render_kpi_card("Pipeline Value", format_currency(pm.total_pipeline_value()), "Open deals")
            pm.close()
        else:
            render_kpi_card("Pipeline Value", "--")

    with kpi_cols[1]:
        if deals_df is not None:
            pm = PipelineMetrics(deals_df)
            render_kpi_card("Active Deals", str(pm.active_deals_count()), "Status: Open")
            pm.close()
        else:
            render_kpi_card("Active Deals", "--")

    with kpi_cols[2]:
        if wo_df is not None:
            from analytics.financial_metrics import FinancialMetrics
            fm = FinancialMetrics(wo_df)
            render_kpi_card("Receivables", format_currency(fm.receivable_amount()), "Outstanding")
            fm.close()
        else:
            render_kpi_card("Receivables", "--")

    with kpi_cols[3]:
        if deals_df is not None:
            pm = PipelineMetrics(deals_df)
            render_kpi_card("Avg Deal Size", format_currency(pm.average_deal_size()), "All open deals")
            pm.close()
        else:
            render_kpi_card("Avg Deal Size", "--")

    st.markdown("")

# =============================================================================
# Main: Chat + Charts
# =============================================================================
col_chat, col_viz = st.columns([1, 1])

with col_chat:
    # Section header with clear button
    hdr_left, hdr_right = st.columns([3, 1])
    with hdr_left:
        st.markdown('<div class="section-header">Ask a business question</div>',
                    unsafe_allow_html=True)
    with hdr_right:
        if st.button("Clear chat", key="clear_chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    user_input = st.chat_input(
        placeholder="e.g. How is our pipeline looking for mining?",
        key="chat_input",
    )

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Process latest unprocessed user message
    if (st.session_state.chat_history
        and st.session_state.chat_history[-1]["role"] == "user"
        and not st.session_state.chat_history[-1].get("processed")):

        last_msg = st.session_state.chat_history[-1]

        if not st.session_state.data_loaded:
            response = {
                "insight": "Please load data first using the sidebar.",
                "nonsensical": False,
                "suggestions": [],
                "warnings": [],
            }
        else:
            with st.spinner("Analyzing..."):
                response = st.session_state.agent.process_query(last_msg["content"])

        last_msg["processed"] = True
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response.get("insight", ""),
            "data": response,
        })
        st.rerun()

    # Render chat history (reversed: newest on top)
    for msg in reversed(st.session_state.chat_history):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            data = msg.get("data", {})

            # Handle nonsensical queries
            if data and data.get("nonsensical"):
                with st.chat_message("assistant"):
                    suggestions = data.get("suggestions", [])
                    suggestions_html = "".join(
                        f'<div class="rephrase-suggestion">{s}</div>'
                        for s in suggestions[:5]
                    )
                    st.markdown(f"""
                    <div class="rephrase-card">
                        <div class="rephrase-title">I couldn't understand that query</div>
                        <div class="rephrase-msg">
                            Your question doesn't seem to relate to business data I can analyze.
                            Please try rephrasing using business terms, or try one of these:
                        </div>
                        {suggestions_html}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                with st.chat_message("assistant"):
                    if msg.get("content"):
                        st.markdown(msg["content"])
                    if data and data.get("warnings"):
                        for w in data["warnings"]:
                            st.markdown(
                                f'<div class="warning-pill">{w}</div>',
                                unsafe_allow_html=True,
                            )

with col_viz:
    st.markdown('<div class="section-header">Visualizations</div>',
                unsafe_allow_html=True)

    # Chart from latest response
    if st.session_state.chat_history:
        latest_assistant = None
        for msg in reversed(st.session_state.chat_history):
            if msg["role"] == "assistant" and msg.get("data"):
                latest_assistant = msg
                break

        if latest_assistant and latest_assistant.get("data"):
            data = latest_assistant["data"]

            # Don't render charts for nonsensical queries
            if not data.get("nonsensical"):
                chart_data = data.get("chart_data")
                chart_type = data.get("chart_type")

                if isinstance(chart_data, pd.DataFrame) and not chart_data.empty and chart_type:
                    render_chart(chart_data, chart_type)

                if data.get("kpis"):
                    kpi_items = data["kpis"]
                    kpi_cols_r = st.columns(min(len(kpi_items), 3))
                    for i, (k, v) in enumerate(kpi_items.items()):
                        with kpi_cols_r[i % 3]:
                            label = k.replace("_", " ").title()
                            if isinstance(v, float) and v > 1000:
                                render_kpi_card(label, format_currency(v))
                            elif isinstance(v, float):
                                render_kpi_card(label, f"{v:.1f}%")
                            else:
                                render_kpi_card(label, str(v))

    # Default charts when data loaded but no query
    if st.session_state.data_loaded and not st.session_state.chat_history:
        agent = st.session_state.agent
        deals_df = agent.get_deals_df()
        wo_df = agent.get_work_orders_df()

        if deals_df is not None:
            pm = PipelineMetrics(deals_df)
            sector_data = pm.pipeline_value_by_sector()
            if not sector_data.empty:
                render_chart(sector_data, "bar_sector")
            stage_data = pm.pipeline_by_stage()
            if not stage_data.empty:
                render_chart(stage_data, "bar_stage")
            pm.close()

        if wo_df is not None:
            from analytics.operational_metrics import OperationalMetrics
            om = OperationalMetrics(wo_df)
            exec_data = om.execution_status_distribution()
            if not exec_data.empty:
                render_chart(exec_data, "pie")
            om.close()


# =============================================================================
# Leadership Update
# =============================================================================
st.markdown("---")
st.markdown('<div class="section-header">Leadership Update</div>',
            unsafe_allow_html=True)

if st.button("Generate Leadership Update", type="primary"):
    if not st.session_state.data_loaded:
        st.warning("Please load data first.")
    else:
        with st.spinner("Generating update..."):
            update = st.session_state.agent.generate_leadership_update()
        st.markdown(f'<div class="insight-card">{update}</div>', unsafe_allow_html=True)
        st.download_button(
            label="Download Update",
            data=update,
            file_name="leadership_update.md",
            mime="text/markdown",
        )

# =============================================================================
# Footer
# =============================================================================
st.markdown("""
<div class="app-footer">
    Monday BI Agent &middot; Streamlit + LangChain + Groq &middot; Llama 3.1
</div>
""", unsafe_allow_html=True)
