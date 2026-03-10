# Monday BI Agent

**AI-Powered Business Intelligence for Founders**

An intelligent BI copilot that connects to Monday.com boards, cleans business data, runs analytics, generates executive insights, and visualizes results through natural language questions.

---

## Architecture

The system uses a modular state-machine approach for processing queries:

1. **Streamlit UI**: Dark-themed dashboard with newest-first chat ordering and interactive Plotly visualizations.
2. **LangGraph Orchestrator**: Manages the flow from query interpretation to analytical execution and final insight generation.
3. **Data Pipeline**: Robust cleaning engine that handles null values, outliers, and data corruption before analysis.
4. **Analytics Engine**: Purpose-built modules for Sales Pipeline, Operations, and Financial metrics.
5. **LLM Layer**: Powered by Groq (Llama 3.1) for high-speed reasoning and natural language generation.

---

## Project Structure

- **app.py**: Main dashboard and UI logic.
- **agent/**: Core intelligence and state machine (LangGraph).
- **data/**: Monday.com API integration and data cleaning pipeline.
- **analytics/**: Specific metric calculators for finance, operations, and sales.
- **config/**: Environment variable management and global constants.
- **utils/**: Shared helpers for logging, currency, and date formatting.
- **decision_log.md**: Documentation of assumptions, trade-offs, and architecture.

---

## Monday.com Board Configuration

The agent is optimized for two primary board types. While it handles variations, the following structure is recommended:

### Deals Board
- **Deal Name**: Primary item title.
- **Deal Status**: Status field (Open, Won, Dead).
- **Masked Deal Value**: Numeric field for revenue calculation.
- **Sector**: Categorical field for industry breakdown.
- **Close Date**: Date field for trend analysis.

### Work Orders Board
- **Execution Status**: Current status of project delivery.
- **Billed Value**: Total amount invoiced.
- **Collected Amount**: Revenue already received.
- **Amount Receivable**: Outstanding payments.

---

## Example Queries

- "How is our pipeline looking for the mining sector this quarter?"
- "What deals are likely to close this month?"
- "Which sectors generate the most revenue?"
- "How much receivable revenue do we have?"
- "What is the billing completion rate?"
- "Show me pipeline by deal stage."

---

## Deployment

The application is deployed on Streamlit Cloud for ease of accessibility and real-time collaboration.

### Configuration on Streamlit Cloud
1. Connect the GitHub repository to the Streamlit dashboard.
2. Add the following environment variables in Advanced Settings:
   - **MONDAY_API_KEY**: Your Monday.com developer token.
   - **GROQ_API_KEY**: Your Groq API key for Llama 3.1.
   - **DEALS_BOARD_ID**: The ID of your sales board.
   - **WORK_ORDERS_BOARD_ID**: The ID of your operations board.

### Maintenance
- The application automatically pulls data from the connected Monday.com boards.
- Use the "Refresh Data" button in the sidebar to sync the latest changes from the CRM.
- For local testing, ensure a .env file is present with the keys mentioned above.
