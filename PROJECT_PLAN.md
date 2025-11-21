# Capstone: Telegram Stock/FX Alerts with AI (Groq) — Project Plan

**Last updated:** 2025-11-04

## 🆕 **MAJOR UPDATE - Separated Alert Architecture v2.2.0**
**Status:** ✅ **COMPLETED** - Production-ready separated alert system with API fallbacks!

### **Latest Features (2025-11-04):**
- **✅ Separated Alert Scheduling**: Individual configurable intervals for each alert type
- **✅ API Rate Limiting & Fallbacks**: Yahoo Finance backup when FMP hits limits  
- **✅ Independent Alert Execution**: Each alert type runs separately, no conflicts
- **✅ Optimal Monitoring Frequency**: Different intervals for different needs
- **✅ Production Stability**: One alert failure doesn't affect others
- **✅ Enhanced Error Handling**: Transparent fallback notifications to users

### **Previous Features (v2.1.x):**
- **✅ Interactive Telegram Commands**: Full two-way communication with user
- **✅ Dynamic Watchlist Management**: Add/remove stocks via Telegram (`/add TSLA`, `/remove AAPL`)  
- **✅ Three-Tier Information System**: 
  - `AAPL` → Brief company summary
  - `/quote AAPL` → Detailed price & metrics
  - `/research AAPL` → Full AI analysis
- **✅ Combined Bot Operation**: Alerts + interactive commands simultaneously
- **✅ Clean Modular Architecture**: Organized into `core/`, `services/`, `analytics/`, `utils/`
- **✅ User-Initiated Research Only**: No automated AI research, only manual requests

This project implements a Telegram bot that:
- Sends **earnings**, **news**, and **price‑spike** alerts for stocks (mirroring the article’s pattern).
- Adds **FX** alerts (e.g., `USDSGD`, `EURUSD` using Yahoo Finance tickers like `USDSGD=X`).  
- Includes an **AI component** (Groq LLM) that synthesizes short explanations over retrieved context.
- Targets **Colab** for iterative testing and **Hugging Face Spaces** (Docker) for deployment.

## 1) Architecture (at a glance)
- **Bot / Command Layer**: `python-telegram-bot` async bot.
- **Schedulers**: polling loops for alerts (earnings, news, spikes, FX).
- **Market Data**:
  - **Stocks**: FinancialModelingPrep (FMP) for earnings & news; yfinance for price bars when convenient.
  - **FX**: yfinance pairs (`XXXYYY=X`) for 1h candles & spike threshold checks.
- **AI Layer (optional)**: Groq chat completions to explain alerts (`/why <symbol>`), and a mini “RAG” over project docs.
- **Persistence**: lightweight JSON logs for dedupe (similar to article).
- **Deploy**: Docker Space on Hugging Face with a FastAPI health endpoint.

## 2) Alerts parity with article
- **Earnings calendar** via FMP; filter only watched tickers.
- **Stock news** via FMP; consolidate & dedupe.
- **Price spikes (1‑hour)** using latest OHLC; if |close‑open|/open * 100 ≥ threshold → alert.
- **Schedule**: run earnings daily, news hourly, spikes each hour; FX alerts on same cadence.

## 3) AI Components
- `/why <SYMBOL>`: calls Groq to explain a recent alert succinctly.
- `/ask <question>`: tiny RAG over `docs/` (FAISS + sentence‑transformers) then Groq summarizes (optional).
- Toggle Groq usage via `.env` (`GROQ_API_KEY`).

## 4) Commands
- `/start` — greet + quick help
- `/watch <SYMBOL>` — add ticker (supports `=X` FX tickers)
- `/unwatch <SYMBOL>` — remove
- `/list` — shows stock and FX watchlists
- `/ask <question>` — RAG Q&A (optional Groq)
- `/why <SYMBOL>` — explain last alert for symbol (Groq)
- `/help` — menu

## 5) Data & Thresholds
- `STOCK_THRESHOLD_PCT` (default `0.5`); `FX_THRESHOLD_PCT` (default `0.2`).
- 1h intervals by default, configurable.
- JSON logs: `earnings_calendar_log.json`, `stock_news_logs.json`, `stock_prices_log.json`, `fx_prices_log.json`.

## 6) Current Architecture Status

### **Clean Modular Design** ✅
```
app/
├── bot_modular.py              # Scheduled alerts
├── core/
│   ├── telegram_client.py      # Telegram API
│   └── interactive_bot.py      # User commands
├── services/
│   ├── ai_research.py          # AI analysis (user-initiated)
│   ├── data_providers.py       # Stock/FX data
│   └── earnings.py             # Earnings monitoring
├── analytics/
│   ├── alerts.py               # Alert systems
│   └── charts.py               # Technical charts
└── utils/
    ├── logs.py                 # Logging
    └── persistence.py          # State management
```

### **Interactive System** ✅
**Three-Tier Information System:**
- **Level 1 (Brief)**: `MSFT` → Company overview & business analysis
- **Level 2 (Quote)**: `/quote MSFT` → Price, volume, market cap, daily change  
- **Level 3 (Full)**: `/research MSFT` → Comprehensive AI investment research

**Available Commands:**
- **Management**: `/add TSLA`, `/remove AAPL`, `/stocks`, `/status`
- **Information**: `TICKER`, `/quote TICKER`, `/research TICKER`
- **Bot Control**: `/help`, `/start`

### **Current System Capabilities (v2.2.0)**

#### **Separated Alert Architecture**
| Alert Type | Interval | Function | Status |
|-----------|----------|----------|--------|
| MA Crossovers | 30 min | Golden/Death Cross detection | ✅ Production |
| 52-Week Highs | 15 min | New milestone tracking | ✅ Production |
| Buy Dips | 10 min | Strategic entry opportunities | ✅ Production |  
| General Stock | 5 min | Real-time price monitoring | ✅ Production |
| Earnings | 10 min | Earnings calendar updates | ✅ Production |

#### **API Resilience System**
- **Primary**: FMP API for comprehensive data
- **Fallback**: Yahoo Finance when FMP rate limited  
- **Rate Limiting**: 500ms delays prevent blocking
- **Error Handling**: Users notified of fallback usage
- **Status**: ✅ Production tested, no more 429 errors

#### **Interactive Features**
- **Three-Tier Info System**: Brief summary → Detailed quote → Full AI analysis
- **Dynamic Watchlist**: Add/remove stocks via Telegram commands
- **Real-time Research**: On-demand AI analysis using Groq LLM
- **Status**: ✅ Full production deployment ready

### **Deployment Options** 
- **Combined System**: `python bot_interactive.py` (alerts + interactive - recommended)
- **Separated Alerts**: `python app/bot_modular.py --continuous`  
- **One-time Test**: `python app/bot_modular.py --once`
- **Production**: Docker + `docker-compose.yml`
- **Cloud**: Environment variables configured
- **Testing**: Individual alert functions + comprehensive system tests
5. Run bot: `!python -u app/bot.py` (polling).

> Colab is for development; it may idle. Use Hugging Face Spaces (paid hardware) or another host for 24/7.

## 7) Hugging Face Spaces (Docker) Deploy
- Space **SDK: Docker**; the container exposes FastAPI at `/` for health.
- Bot runs in background thread (polling). Configure secrets in Space Settings.

## 8) Project Structure
```
.
├─ README.md
├─ PROJECT_PLAN.md   ← this file
├─ .env.example
├─ requirements.txt
├─ Dockerfile
├─ docker-compose.yml         # optional for local
├─ app/
│  ├─ bot.py
│  ├─ config.py
│  ├─ utils/
│  │  ├─ persistence.py
│  │  └─ logs.py
│  ├─ providers/
│  │  ├─ fmp.py               # earnings/news
│  │  ├─ prices.py            # yfinance price helpers (stocks + FX)
│  ├─ alerts/
│  │  ├─ earnings.py
│  │  ├─ news.py
│  │  ├─ spikes.py            # stock 1h spike
│  │  └─ fx_spikes.py         # fx 1h spike
│  ├─ ai/
│  │  ├─ groq_client.py
│  │  ├─ explain.py           # /why
│  │  └─ rag/
│  │     ├─ ingest.py
│  │     ├─ qa.py
│  │     └─ docs/
│  │        ├─ alerts.md
│  │        └─ indicators.md
│  └─ run_hf.py               # FastAPI + background bot
└─ notebooks/
   └─ colab_bootstrap.ipynb
```

## 9) Risks & mitigations
- **API Limits/Latency:** Implement retry/backoff; cache last responses.
- **Data quality (free feeds):** Treat alerts as informational; show “delayed” disclaimers.
- **Uptime:** Prefer always-on host for production alerts.

## 10) Roadmap
- Add indicators (RSI/MA crossovers), 52‑week breakouts.
- Vendor websockets for lower latency.
- User-scoped watchlists (DB), admin panel.
- News summarization via Groq, embeddings‑backed symbol knowledge.
