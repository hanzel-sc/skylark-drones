# Decision Log - Monday BI Agent

## 1. Key Assumptions

### Data Integrity and Structure
- Monday.com Board Schema: We assume boards follow the standard enterprise schema for "Deals" and "Work Orders". Column names may vary slightly, which is why a robust alias mapping system was implemented.
- Financial Representation: All currency values are treated as absolute numbers in INR. We assume that if a value is "negative" in the source, it represents a data entry error and should be corrected to zero to prevent skewing aggregate analytics.
- Date Formats: We assume date strings are in standard ISO format or common regional variations (DD-MM-YYYY) and use safe parsing to handle edge cases.

### Infrastructure
- API Availability: While the system is designed for real-time Monday.com integration, we assume a CSV fallback is critical for reliability during API rate-limiting or authentication failures.
- LLM Reliability: We assume that Llama 3.1 8B is capable of consistent structured JSON output when prompted with strict schema definitions.

---

## 2. Trade-offs and Rationale

### LangGraph vs Linear Orchestration
- Choice: Migrated from a linear Python script to a LangGraph state machine.
- Rationale: A linear script creates "all-or-nothing" failures. LangGraph allows us to define clear nodes (Interpret -> Execute -> Insight) and route "nonsensical" queries directly to a fallback node, saving time and compute resources.
- Trade-off: Increased complexity in the codebase, but improved fault tolerance and observability.

### In-Memory vs Database Persistence
- Choice: Used Pure Pandas and DuckDB for in-memory processing.
- Rationale: For an executive BI tool, the data volume (~350-500 rows) does not justify a permanent SQL database like PostgreSQL. DuckDB allows us to perform high-speed SQL-like aggregations on memory DataFrames without the infrastructure overhead.
- Trade-off: Data must be re-loaded on app startup, though this is mitigated by Streamlit's session caching.

### Groq (Llama 3.1) vs OpenAI (GPT-4)
- Choice: Groq API with Llama 3.1 8B Instant.
- Rationale: Latency is a primary user experience driver. Groq delivers sub-second inference, making the chat interface feel responsive. Llama 3.1 8B is sufficiently intelligent for query classification and narrative summarization.
- Trade-off: Slight reduction in complex reasoning capabilities compared to GPT-4, though this is offset by specific system prompting and safe-guards.

---

## 3. Interpretation of "Leadership Updates"

The "Leadership Update" feature was implemented as a comprehensive summary designed for a founder or CXO. My interpretation included:
- Top-Down View: Prioritizing the "Total Pipeline Value" and "Total Receivables" as the primary health indicators.
- Operational Pulse: Including "Billing Completion Rate" to show how much work is actually being converted to cash.
- Exception Reporting: Automatically identifying the "Top Performing Sector" and "Deals in Negotiation" to highlight where executive focus should be directed.
- Strategic Narrative: Using the LLM to synthesize these numbers into a professional markdown report rather than just a list of KPIs.

---

## 4. Future Improvements (What I'd do differently with more time)

### Technical Scaling
- RAG for Documentation: I would implement a Retrieval-Augmented Generation (RAG) layer to allows founders to ask questions about internal PDF reports or contracts alongside their Monday.com data.
- Automated Mapping: Currently, column aliases are manual. I would implement a "fuzzy-matching" or LLM-based column mapper that automatically identifies relevant board columns without configuration.

### User Experience
- Real-time Webhooks: Instead of manual refreshes, I would implement Monday.com webhooks to push updates to the dashboard in real-time.
- Multi-User Isolation: Implement a proper auth layer with Row-Level Security (RLS) so different department heads only see their respective data.

### Analytics Depth
- Predictive Modeling: I would add a "Predictive Closure" metric that uses historical data to estimate the likelihood of a deal closing based on its age and stage, rather than relying on the "Closure Probability" field which is often subjective.
