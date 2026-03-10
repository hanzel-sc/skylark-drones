# Monday BI Agent

AI-Powered Business Intelligence for Founders

The Monday BI Agent is a specialized decision-support system designed to transform raw operations and sales data from Monday.com into actionable executive insights. By combining the speed of the Groq inference engine with the structured orchestration of LangGraph, the agent provides a natural language interface for complex business analytics.

---

## Technical Architecture

The application follows a modular, layer-based architecture designed for high throughput and reliable data interpretation.

```
[ User Layer ]
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Streamlit Application                                           │
│ ─ UI Components (Dark Dashboard, Interactive Charts)            │
│ ─ Session State Management (Data Caching, History)              │
│ ─ Visualization Layer (Plotly Express, Graph Objects)           │
└─────────────────────────────────────────┬───────────────────────┘
                                          │
                                          ▼
[ Orchestration Layer ]
┌─────────────────────────────────────────────────────────────────┐
│ LangGraph State Machine                                         │
│                                                                 │
│ ┌───────────────┐       ┌───────────────┐       ┌───────────────┐│
│ │   Interpret   │ ─────▶│    Execute    │ ─────▶│   Generate    ││
│ │    (Node)     │       │    (Node)     │       │    (Node)     ││
│ └───────┬───────┘       └───────┬───────┘       └───────┬───────┘│
│         │                       │                       │        │
│         ▼                       ▼                       ▼        │
│  QueryInterpreter       Analytics Engine        InsightGenerator │
│  (NL Intent Map)       (Metric Modules)        (LLM Narrative)   │
└─────────────────────────────────┬────────────────────────────────┘
                                  │
                                  ▼
[ Data Intelligence Layer ]
┌─────────────────────────────────────────────────────────────────┐
│ Monday.com API Client (v2024-10)                                │
│ ─ GraphQL Query Builder (Nested Column Values)                  │
│ ─ CSV Fallback Recovery System                                  │
│                                                                 │
│ Data Cleaning Pipeline                                          │
│ ─ Outlier Detection (Z-Score & Std Dev)                         │
│ ─ Type Enforcement & Schema Normalization                       │
│ ─ Composite-Key Duplicate Removal                                │
│ ─ String Sanitization & Business Alias Mapping                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1. Intelligence Discovery (interpret)
The system uses Llama 3.1 8B via Groq to perform semantic analysis on user queries. It extracts:
- Metric Type (e.g., Pipeline Value, Billing Rate, Receivables)
- Filters (Sector, Time Period, Client)
- Intent Validity (Detects nonsensical or off-topic queries)

### 2. Analytical Execution (execute)
Once intent is mapped, the agent invokes specialized analytics modules. These modules utilize Pandas and DuckDB to perform high-speed aggregations on the cleaned dataframes. Areas covered:
- Sales Pipeline (Funnel analysis, deal trends)
- Operational Efficiency (Work order status distribution, execution rates)
- Financial Health (Billing vs. Collection, Outstanding receivables)

### 3. Insight Synthesis (generate)
The final node takes raw data summaries and identifies strategic anomalies or successes. The LLM translates these findings into executive-level prose, highlighting specific areas for concern or celebration.

---

## Project Structure and Modules

### Application Core
- **app.py**: The frontend entry point. Manages the dual-column layout (Chat vs. Visualizations) and handles user sessions.
- **agent/agent.py**: Implements the StateGraph. Defines how data moves between nodes and manages the lifecycle of a query.

### Data and Analytics
- **data/monday_client.py**: Handles authentication and pagination with the Monday.com API. Includes error handling for breaking GraphQL changes.
- **data/data_cleaning.py**: Implements the DataCleaner class. This is where business logic for data integrity resides, including negative value correction and sector normalization.
- **analytics/pipeline_metrics.py**: Logic for calculating pipeline value, active deal counts, and stage-specific metrics.
- **analytics/operational_metrics.py**: Computes work order volume and completion rates across different sectors.
- **analytics/financial_metrics.py**: Analyzes billing cycles, collection efficiency, and financial summaries.

### Configuration and Utilities
- **config/settings.py**: Centralized configuration management. Contains environment mappings, sector aliases, and deal stage order.
- **utils/helpers.py**: Shared utility functions for formatting large currency values (Lakhs/Crores), parsing inconsistent date formats, and safety-checking floats.
- **utils/logging.py**: Structured JSON logging for monitoring agent performance and API stability.

---

## Data Governance and Cleaning

The system enforces strict data integrity through a multi-pass cleaning pipeline:
- **Standardization**: Columns are mapped from raw Monday.com titles to internal standardized identifiers using a configurable alias dictionary.
- **Integrity**: Finance-critical fields undergo type enforcement. Non-numeric values in numeric columns are coerced to zero or default values based on business importance.
- **Context Preservation**: While cleaning, the system tracks "Data Quality Warnings" (e.g., missing sectors or potential outliers) and surfaces them alongside the AI insights to ensure transparency for the end-user.

---

## Key Performance Indicators (KPIs)

The agent supports real-time calculation of several executive KPIs:
- **Pipeline Value**: Total potential revenue from open deals.
- **Billing Completion**: Percentage of work order value that has been successfully invoiced.
- **Collection Rate**: Ratio of billed revenue that has been successfully collected.
- **Receivables**: Total outstanding payments due from clients.
- **Deal Velocity**: Creation trends and stage-progression speed.
