# Decision Log — Monday BI Agent

## 1. Key Assumptions

### Data Structure
- Monday.com boards follow the specified column structure (Deals and Work Orders).
- CSV files serve as fallback when the Monday.com API is unavailable.
- The Work Orders CSV has an extra blank header row (row 0) that must be skipped during ingestion.
- Deal values are masked/anonymized but remain numerically meaningful for analytics.

### Business Logic
- "Active" deals are those with status = "Open".
- Pipeline value includes only deals with `deal_value > 0` and `deal_status = 'Open'`.
- "Current quarter" is based on calendar quarters (Q1: Jan-Mar, Q2: Apr-Jun, etc.).
- Closure probability levels (High/Medium/Low) are categorical, not numeric.
- Financial amounts are in Indian Rupees (₹) and should be displayed using Lakhs (L) and Crores (Cr) notation.

### Agent Behavior
- The LLM interprets user intent into one of ~15 predefined metrics.
- Unknown or conversational queries fall back to `general_query` with context-based response.
- The system always generates a human-readable insight alongside raw data.

---

## 2. Tradeoffs

### LangGraph State Machine
- **Chose LangGraph**: Replaced linear orchestrator with a state graph (`interpret` -> `execute` -> `insight`).
- **Rationale**: Better control over multi-hop reasoning, error handling, and future scalability for tool-calling agents.

### DuckDB vs SQLite vs Pure Pandas
- **Chose DuckDB**: Provides SQL-like analytics on DataFrames without persistence overhead. Ideal for analytical queries on in-memory data.
- **Tradeoff**: Adds a dependency, but the performance and expressiveness gains are significant for complex aggregations.

### Groq (Llama 3.1) vs OpenAI
- **Chose Groq with Llama 3.1 8B Instant**: Fast inference (~200ms), cost-effective, good at structured JSON output.
- **Tradeoff**: Smaller context window and less sophisticated reasoning than GPT-4, but sufficient for query interpretation and insight generation in this use case.

### Streamlit vs Dash vs Custom React Frontend
- **Chose Streamlit**: Rapid prototyping, built-in chat UI, native Python, zero frontend build step. Ideal for an internal BI tool.
- **Tradeoff**: Less customizable than a React frontend; limited real-time capabilities. Acceptable for a founder-facing dashboard.

### Monday.com API vs Direct Database
- **Chose Monday.com GraphQL API**: The requirement mandates dynamic board querying. No separate database is maintained.
- **Tradeoff**: API rate limits and latency. Mitigated with CSV fallback and in-memory caching after initial load.

### CSV Fallback Strategy
- **Decision**: Support both API and CSV data sources with automatic CSV detection.
- **Rationale**: The Monday.com API may be unavailable during development/testing. CSVs provide deterministic data for testing and demos.

---

## 3. Design Decisions

### LangGraph Orchestration
The agent uses a structured graph to manage state transitions. This prevents linear bottlenecks and allows for branching logic (e.g., routing nonsensical queries directly to the rephrase node without hitting the analytics engine).

### Modern Dark UI (Aceternity-Inspired)
- **Palette**: Professional high-contrast dark theme using Cyan/Teal accents (#66FCF1) on a Zinc/Deep-Charcoal base (#0B0C10, #1F2833).
- **Typography**: Universal Inter font for a professional SaaS feel.
- **Ordering**: Newest-first chat ordering ensures the most recent insight is always at the top of the viewport.

### Advanced Data Preprocessing
The pipeline in `DataCleaner` now handles:
- **Outlier Detection**: Flagging unusually high deal values (3+ Std Dev).
- **Type Enforcement**: Coercing strings/nulls to proper float64 for financial accuracy.
- **Corrupted Data Correction**: Fixing negative financial values and stripping non-business characters from sectors.
- **Duplicate Removal**: Stripping redundant records based on composite keys.

### Two-Phase LLM Processing
1. **Query Interpretation** (structured JSON output): Converts natural language to a metric identifier with filters.
2. **Insight Generation** (narrative text): Converts raw analytics results to executive prose.

This separation ensures deterministic analytics (no hallucinated numbers) while leveraging LLM strengths for natural language.

### Error-Resistant Ingestion
- **API v2024-10 Compatibility**: Updated GraphQL queries to nested `column { title }` structure to resolve breaking changes in the Monday.com API.
- **Multi-Layer Validation**: Gibberish pre-detection, short-query filtering, and metric mapping fallback.

### Session State for Caching
- Streamlit's `session_state` caches the agent, loaded data, and chat history.
- Data is loaded once and reused across queries until explicitly refreshed.

### KPI + Chart + Insight Trifecta
Every query response includes three components:
1. **KPI cards**: Quick numeric summary
2. **Charts**: Visual data representation
3. **AI Insight**: Executive-level narrative interpretation

---

## 4. Future Improvements

### Short-Term
- **Auto-discover board IDs**: Use the Monday.com API to list boards and match by name instead of requiring manual ID input.
- **Caching layer**: Add Redis or in-memory TTL cache for API responses to reduce Monday.com API calls.
- **Export capabilities**: Add PDF export for leadership updates and Excel export for data tables.

### Medium-Term
- **Multi-board joins**: Enrich deals data with work order data for cross-board analytics (e.g., "Which won deals have the highest receivables?").
- **Historical tracking**: Store snapshots of board data over time to enable trend analysis.
- **Custom alerts**: Set up threshold-based alerts (e.g., "Notify when receivables exceed ₹50L").
- **User authentication**: Add Streamlit authentication to restrict access to authorized users.

### Long-Term
- **RAG integration**: Index board data and past insights for more contextual LLM responses.
- **Predictive analytics**: Use historical deal data to predict deal closure probabilities using ML models.
- **Real-time sync**: Implement webhooks to receive Monday.com board updates in real-time.
- **Multi-tenant support**: Support multiple Monday.com accounts with tenant isolation.
- **Custom metric builder**: Allow users to define custom KPIs and analytics queries through the UI.
