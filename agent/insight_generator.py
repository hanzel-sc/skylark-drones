"""
Insight Generator Module.
Uses Groq LLM (Llama 3.1) to generate executive-level business insights
from analytical results.
"""

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from config.settings import settings
from utils.logging import get_logger

logger = get_logger(__name__)

INSIGHT_SYSTEM_PROMPT = """You are an executive business intelligence advisor for Skylark, a drone services company.

Given analytical results, generate concise, actionable executive insights.

Guidelines:
- Be direct and data-driven
- Highlight key findings, trends, and risks
- Use specific numbers and percentages
- Suggest actions when applicable
- Format amounts in Indian Rupees (₹) using Lakhs (L) and Crores (Cr) notation
- Keep the response concise (3-5 bullet points max)
- Use markdown formatting for clarity
- Focus on what matters to a founder/CEO

Do NOT make up numbers. Only use the data provided.
If data seems incomplete, mention that clearly.
"""

LEADERSHIP_SYSTEM_PROMPT = """You are a senior business analyst preparing a weekly executive update for the CEO of Skylark, a drone services company.

Generate a structured leadership update with these sections:

## Weekly Sales & Delivery Update

### Pipeline Overview
- Total pipeline value
- Top sectors by pipeline value
- Count of active deals

### Operational Highlights
- Active work orders count
- Billing completion rate
- Key execution status insights

### Financial Highlights
- Total billed and collected
- Outstanding receivables
- Collection rate

### Risks & Attention Items
- Deals stuck in negotiation
- Large pending receivables
- Any data quality issues

Use specific numbers. Format amounts in ₹ with Lakhs (L) / Crores (Cr).
Be concise and executive-friendly.
"""


class InsightGenerator:
    """Generates executive insights from analytical results using LLM."""

    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.LLM_MODEL,
            temperature=0.3,
            max_tokens=settings.LLM_MAX_TOKENS,
        )

    def generate_insight(self, query: str, data_summary: str) -> str:
        """
        Generate an executive insight from analytical results.

        Args:
            query: The original user question.
            data_summary: Formatted summary of the analytical results.

        Returns:
            LLM-generated insight text.
        """
        logger.info("Generating insight for query")

        messages = [
            SystemMessage(content=INSIGHT_SYSTEM_PROMPT),
            HumanMessage(content=f"""
User Question: {query}

Analytical Results:
{data_summary}

Generate a concise executive insight based on these results.
"""),
        ]

        try:
            response = self.llm.invoke(messages)
            insight = response.content.strip()
            logger.info(f"Generated insight ({len(insight)} chars)")
            return insight
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return f"⚠️ Unable to generate AI insight at this time. Error: {str(e)}"

    def generate_leadership_update(self, metrics_summary: str) -> str:
        """
        Generate a comprehensive leadership update.

        Args:
            metrics_summary: Formatted summary of all key metrics.

        Returns:
            Structured leadership update text.
        """
        logger.info("Generating leadership update")

        messages = [
            SystemMessage(content=LEADERSHIP_SYSTEM_PROMPT),
            HumanMessage(content=f"""
Here are the latest business metrics:

{metrics_summary}

Generate a professional weekly leadership update.
"""),
        ]

        try:
            response = self.llm.invoke(messages)
            update = response.content.strip()
            logger.info(f"Generated leadership update ({len(update)} chars)")
            return update
        except Exception as e:
            logger.error(f"Leadership update generation failed: {e}")
            return f"⚠️ Unable to generate leadership update. Error: {str(e)}"

    def generate_conversational_response(self, query: str, context: str) -> str:
        """
        Generate a conversational response for general queries.

        Args:
            query: The user's question.
            context: Available data context.

        Returns:
            Conversational response.
        """
        messages = [
            SystemMessage(content="""You are a friendly, knowledgeable business intelligence assistant
for Skylark, a drone services company. Answer the user's question based on the available data.
Be helpful, concise, and professional. If you don't have enough data to answer,
say so clearly and suggest what data might help."""),
            HumanMessage(content=f"""
Question: {query}

Available Context:
{context}
"""),
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error(f"Conversational response failed: {e}")
            return "I'm sorry, I couldn't process that question. Please try rephrasing it."
