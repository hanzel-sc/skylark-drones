# 🚀 Monday BI Agent

**AI-Powered Business Intelligence for Founders**

An intelligent BI copilot that connects to Monday.com boards, cleans messy business data, runs analytics, generates executive insights, and visualizes results — all through natural language questions.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────┐
│                 Streamlit UI (Dark)              │
│  ┌─────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Chat (T)│ │ KPI Cards│ │ Vibrant Charts   │  │
│  │ New Top │ │          │ │                  │  │
│  └────┬────┘ └──────────┘ └──────────────────┘  │
│       │                                          │
├───────┼──────────────────────────────────────────┤
│       ▼                                          │
│  ┌─────────────────┐                             │
│  │ LangGraph       │  State Machine Orchestrator │
│  │ Orchestrator    │  (Interpret → Execute → Insight)│
│  └────┬────┘────┬──┘                             │
│       │         │                                │
│       ▼         ▼                                │
│  ┌──────────┐ ┌──────────────┐                   │
│  │ Monday.com│ │ Preprocessing│                   │
│  │ API (v2.4)│ │ & Cleaning   │                   │
│  └──────────┘ └──────┬───────┘                   │
│                      ▼                           │
│  ┌──────────────────────────────────┐            │
│  │ Analytics Engine (Pipeline/Ops)  │            │
│  └──────────────┬───────────────────┘            │
│                 ▼                                │
│  ┌─────────────────┐                             │
│  │ Insight Gen     │  Llama 3.1 Reasoning        │
│  └─────────────────┘                             │
└──────────────────────────────────────────────────┘
```

## ⚡ Tech Stack

| Layer | Technology |
|-------|-----------|
| **UI** | Streamlit |
| **Backend** | Python 3.11, Pandas |
| **Analytics** | DuckDB |
| **AI** | LangChain + Groq (Llama 3.1) |
| **Visualization** | Plotly |
| **Data Source** | Monday.com GraphQL API |
| **Infrastructure** | Docker |

---

## 📂 Project Structure

```
monday-bi-agent/
├── app.py                          # Streamlit dashboard
├── agent/
│   ├── agent.py                    # Main agent orchestrator
│   ├── query_interpreter.py        # NL → structured intent
│   └── insight_generator.py        # Analytics → executive insights
├── data/
│   ├── monday_client.py            # Monday.com GraphQL client
│   └── data_cleaning.py            # Data normalization pipeline
├── analytics/
│   ├── pipeline_metrics.py         # Sales pipeline analytics
│   ├── operational_metrics.py      # Work order analytics
│   └── financial_metrics.py        # Billing/collection analytics
├── config/
│   └── settings.py                 # Configuration & env vars
├── utils/
│   ├── logging.py                  # Structured logging
│   └── helpers.py                  # Date, currency, utility functions
├── docker/
│   ├── Dockerfile                  # Container setup
│   └── docker-compose.yml          # Compose configuration
├── requirements.txt                # Python dependencies
├── decision_log.md                 # Architecture decisions
├── .env.example                    # Environment variable template
└── README.md                       # This file
```

---

## 🚀 Setup & Run Locally

### Prerequisites
- Python 3.11+
- Conda (recommended) or pip

### 1. Create Environment

```bash
conda create -n monday-bi python=3.11 -y
conda activate monday-bi
```

### 2. Install Dependencies

```bash
cd monday-bi-agent
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

**Required environment variables:**
| Variable | Description |
|----------|-------------|
| `MONDAY_API_KEY` | Monday.com API token |
| `GROQ_API_KEY` | Groq API key for Llama 3.1 |
| `DEALS_BOARD_ID` | *(Optional)* Monday.com Deals board ID |
| `WORK_ORDERS_BOARD_ID` | *(Optional)* Monday.com Work Orders board ID |

### 4. Place CSV Data Files

Ensure the CSV data files are in the **parent directory** of `monday-bi-agent/`:

```
skylark-2/
├── Deal_funnel_Data.csv
├── Work_Order_Tracker_Data.csv
└── monday-bi-agent/
    └── ...
```

### 5. Run the Application

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🐳 Docker

### Build & Run

```bash
cd monday-bi-agent/docker
docker-compose up --build
```

### Environment Variables for Docker

Create a `.env` file in the `docker/` directory:

```env
MONDAY_API_KEY=your_key
GROQ_API_KEY=your_key
```

---

## 📊 Monday.com Board Configuration

### Deals Board

The agent expects a board with these columns:

| Column | Type |
|--------|------|
| Deal Name | Text |
| Owner code | Text |
| Client Code | Text |
| Deal Status | Status (Open/Dead/Won/On Hold) |
| Close Date (A) | Date |
| Closure Probability | Status (High/Medium/Low) |
| Masked Deal value | Number |
| Tentative Close Date | Date |
| Deal Stage | Status |
| Product deal | Text |
| Sector/service | Text |
| Created Date | Date |

### Work Orders Board

| Column | Type |
|--------|------|
| Deal name masked | Text |
| Customer Name Code | Text |
| Serial # | Text |
| Nature of Work | Text |
| Execution Status | Status |
| Sector | Text |
| Amount in Rupees (Excl of GST) | Number |
| Billed Value in Rupees | Number |
| Collected Amount | Number |
| Amount to be billed | Number |
| Amount Receivable | Number |
| Invoice Status | Status |
| ... *(see full spec)* | |

---

## 💬 Example Queries

| Query | What it does |
|-------|-------------|
| "How is our pipeline looking for the mining sector this quarter?" | Pipeline by sector with quarter filter |
| "What deals are likely to close this month?" | Deals with close date in current month |
| "Which sectors generate the most revenue?" | Pipeline value breakdown by sector |
| "How much receivable revenue do we have?" | Total outstanding receivables |
| "What is the billing completion rate?" | Billed vs total contract value |
| "Show me pipeline by deal stage" | Funnel visualization by stage |
| "What's our deal creation trend?" | Monthly deal creation line chart |

---

## 🚢 Deployment Options

### 1. Streamlit Community Cloud (Easiest)
1. Push your code to a GitHub repository.
2. Sign in to [Streamlit Cloud](https://share.streamlit.io/).
3. Connect your repo and branch.
4. Add your secrets (`MONDAY_API_KEY`, `GROQ_API_KEY`, etc.) in the Cloud dashboard under **Advanced Settings**.
5. Deploy!

### 2. Render / Railway (PAAS)
Both platforms detect the `requirements.txt` and `app.py` automatically.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- **Port**: Usually `8501` or managed by `$PORT`.

### 3. Docker (Enterprise)
The project includes a production-ready `docker/Dockerfile`.
```bash
docker build -t monday-bi .
docker run -p 8501:8501 --env-file .env monday-bi
```

### 4. AWS App Runner / ECS
Best for high-availability production use.
1. Deploy the Docker image to **AWS ECR**.
2. Create an **AWS App Runner** service pointing to the ECR image.
3. Configure the **Port** to `8501`.
4. Add **Environment Variables** for the API keys.
5. Use the provided health check path: `/_stcore/health`.

---

## 📄 License

Internal project — Skylark Drones
