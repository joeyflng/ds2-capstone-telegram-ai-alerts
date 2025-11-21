# 🤖 AI-Powered Stock Market Intelligence Platform

> **Dual-Platform Solution:** Interactive Telegram bot for 24/7 automated monitoring + Web application for on-demand analysis with AI chat

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![HuggingFace](https://img.shields.io/badge/🤗%20HuggingFace-Live%20Demo-yellow)](https://huggingface.co/spaces/starryeyeowl/dsai-2-ai-market-chat)

---

## 🎯 **Project Overview**

A comprehensive stock market intelligence system combining **automated Telegram alerts** with an **AI-powered web interface** for real-time market analysis. Built for traders, investors, and financial analysts who need professional-grade insights with minimal effort.

### **What Makes This Unique?**

- 🔄 **Hybrid Data System**: FMP + Yahoo Finance with automatic failover and rate limiting
- 🧠 **AI-Powered Analysis**: Groq LLM integration for ultra-fast market insights (llama-3.1-8b)
- 📊 **Professional Metrics**: 52-week analysis from FMP API, annualized volatility, RSI, trend signals
- 😱 **Market Sentiment**: Multi-factor VIX-based calculation (not just fear & greed index)
- ⚡ **Performance Optimized**: Session state caching, company name auto-caching (zero extra API calls)
- 🎨 **Clean UX**: Sidebar organization, no page refreshes, mobile-responsive
- 🐳 **Docker Ready**: One-command deployment to Hugging Face Spaces

---

## 🌟 **Key Features**

### 🤖 **Interactive Telegram Bot**
- **Two-Way Communication**: Send commands directly via Telegram
- **Dynamic Watchlist Management**: `/add TSLA`, `/remove AAPL` commands
- **Three-Tier Information System**:
  - `AAPL` → Brief company summary
  - `/quote AAPL` → Detailed price & metrics
  - `/research AAPL` → Full AI analysis
- **Smart Symbol Recognition**: Instant research by ticker symbol
- **Company Name Display**: Shows "TSLA - Tesla, Inc." in stock lists

### 📈 **Automated Alert System**
- **Moving Average Crossovers**: Golden Cross/Death Cross detection
- **52-Week High Alerts**: New milestone tracking
- **Buy Dip Opportunities**: Strategic entry point detection
- **Stock Price Monitoring**: Real-time price change alerts
- **Earnings Calendar**: Upcoming earnings notifications (every 6 hours)
- **Configurable Intervals**: Individual scheduling for each alert type
- **Advanced Rate Limiting**: 40-minute staggered startup prevents API flooding
- **Global Rate Protection**: 30s minimum spacing between alert types
- **Per-Stock Delays**: 15s between individual stock queries

### 🌐 **Interactive Web Application**

**Live Demo**: https://huggingface.co/spaces/starryeyeowl/dsai-2-ai-market-chat

- **Real-Time Market Data**: Live prices via FMP (primary) + Yahoo Finance (fallback)
- **Hybrid Data System**: Automatic failover between FMP and Yahoo for reliability
- **52-Week Analysis**: High/low tracking with position indicators from FMP yearHigh/yearLow
- **Market Sentiment**: Multi-factor VIX-based calculation (VIX 17-24 neutral, S&P 500 momentum, treasury yields, market breadth)
- **AI Chat Assistant**: Ask natural language questions about stocks using Groq AI
- **Interactive Charts**: Professional Plotly visualizations with candlesticks and volume
- **Technical Indicators**: RSI, volatility, moving averages, trend signals
- **Smart Caching**: Session-based data caching + company name auto-caching
- **Telegram Integration**: Sidebar command generator without page refresh
- **Company Names**: Auto-cached from FMP quotes (zero extra API calls)
- **System Info Panel**: Debug panel showing API configuration status

### 🧠 **AI-Powered Research Engine**
- **LLM Integration**: Groq AI for ultra-fast analysis
- **Context-Aware**: AI receives current market data
- **Professional Reports**: Structured insights with recommendations

### 📊 **Visual Analytics**
- **Interactive Plotly Charts**: Web-based price tracking
- **Telegram Integration**: Charts delivered to chat
- **Professional Styling**: Clean, focused metrics display

---

## 📊 **Platform Features Comparison**

| Feature | 🤖 Telegram Bot | 🌐 Web App | 
|---------|----------------|-------------|
| **Real-time Alerts** | ✅ Automated scheduled alerts | ❌ Manual analysis only |
| **Interactive Commands** | ✅ `/add`, `/quote`, `/research` | ✅ Point-and-click interface |
| **AI Analysis** | ✅ Company research via chat | ✅ Interactive AI assistant |
| **Technical Charts** | ✅ Auto-generated & sent | ✅ Interactive Plotly charts |
| **Stock Monitoring** | ✅ 24/7 background monitoring | ✅ On-demand analysis |
| **52-Week High/Low** | ✅ Alerts & tracking | ✅ FMP API yearHigh/yearLow |
| **Market Sentiment** | ❌ No | ✅ Multi-factor VIX calculation |
| **Annualized Volatility** | ❌ No | ✅ 30-day historical |
| **Company Names** | ✅ Auto-cached from FMP | ✅ Auto-cached (zero API calls) |
| **Session Caching** | N/A | ✅ Performance optimized |
| **Mobile Access** | ✅ Native Telegram mobile | ✅ Mobile-responsive web |
| **Setup Complexity** | ⚠️ Telegram bot creation required | ✅ Simple web interface |
| **Deployment** | Local/server required | ✅ Hugging Face Spaces |
| **Use Case** | Production monitoring | Research & education |

---

## 🚀 **Quick Start**

### **Web App (Hugging Face Spaces)**

**Live Demo**: https://huggingface.co/spaces/starryeyeowl/dsai-2-ai-market-chat

No installation needed! Access the web app directly on Hugging Face.

### **Local Web App**

```bash
# Navigate to web app directory
cd market-chat-web

# Install dependencies
pip install -r requirements.txt

# Create .env file with API keys
cp .env.example .env
# Edit .env and add GROQ_API_KEY and FMP_API_KEY

# Run the app
streamlit run app.py
```

### **Telegram Bot**

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GROQ_API_KEY, FMP_API_KEY

# Run the bot
python app/bot_modular.py
```

---

## 📦 **Detailed Installation & Setup**

### **System Requirements**
- **Python**: 3.11+ (tested on 3.11, 3.13)
- **Operating System**: Linux, macOS, Windows
- **Memory**: 1GB+ (recommended for chart generation)
- **APIs**: Telegram Bot Token (bot), Groq API Key, FMP API Key

### **Step 1: Clone Repository**
```bash
git clone https://github.com/joeyflng/ds2-capstone-telegram-ai-alerts.git
cd ds2-capstone-telegram-ai-alerts
```

### **Step 2: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 3: Configure API Keys**

Create `.env` file in the root directory:

```env
# Required for both bot and web app
GROQ_API_KEY=your_groq_api_key_here
FMP_API_KEY=your_fmp_api_key_here

# Required only for Telegram bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional
FMP_DELAY_SECONDS=3
```

**Get API Keys:**
- **Groq**: https://console.groq.com/keys (free tier available)
- **FMP**: https://financialmodelingprep.com/developer/docs (paid plan recommended for yearHigh/yearLow)
- **Telegram Bot**: Talk to @BotFather on Telegram
- **Chat ID**: Send `/start` to @userinfobot

---

## 🌐 **Web App Deployment**

### **Hugging Face Spaces**

```bash
cd market-chat-web
./deploy_to_hf.sh
```

This automated script:
1. Copies all files to HF repo (including critical `app/` folder)
2. Shows changes and prompts for confirmation
3. Pushes to HF, triggering Docker rebuild

**⚠️ Critical:** Dockerfile MUST include:
```dockerfile
COPY app/ ./app/  # Required for FMP hybrid APIs
```

Without this line, web app uses mock data instead of real FMP data.

**Verification:**
Check Container logs for:
```
App folder exists: True
✅ Added app path: /app/app (services found)
✅ Hybrid FMP+Yahoo APIs loaded successfully
```

**See**: [market-chat-web/HUGGINGFACE_DEPLOY.md](market-chat-web/HUGGINGFACE_DEPLOY.md) for detailed instructions.

---

## 📁 **Project Structure**

```
ds2-capstone-telegram-ai-alerts/
├── app/                        # Telegram Bot Backend
│   ├── bot_modular.py         # Main bot entry point
│   ├── config.py              # Bot configuration
│   ├── core/
│   │   ├── interactive_bot.py # Command handlers
│   │   └── telegram_client.py # Telegram API wrapper
│   ├── services/
│   │   ├── fmp_hybrid.py      # FMP + Yahoo hybrid with caching
│   │   ├── data_providers.py  # Unified data fetching
│   │   ├── market_sentiment.py # VIX-based sentiment
│   │   ├── ai_research.py     # Groq AI integration
│   │   └── earnings.py        # Earnings calendar
│   ├── analytics/
│   │   ├── alerts.py          # Alert system (MA, 52W, dips)
│   │   └── charts.py          # Chart generation
│   └── data/
│       ├── stock_list.txt     # Monitored stocks
│       └── fx_list.txt        # FX pairs
│
├── market-chat-web/            # Web Application
│   ├── app.py                 # Streamlit app (inline config + patch)
│   ├── Dockerfile             # Docker config (MUST copy app/ folder)
│   ├── requirements.txt       # Python dependencies
│   ├── deploy_to_hf.sh        # Automated HF deployment script
│   ├── utils/
│   │   ├── market.py          # Market data (auto-detects app/ folder)
│   │   └── llm.py             # AI chat integration
│   └── [shares app/ folder with bot for FMP services]
│
├── requirements.txt            # Main project dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

---

## 🔧 **Configuration**

### **Telegram Bot Configuration**

Edit `app/data/stock_list.txt` to customize monitored stocks:
```
AAPL
TSLA
NVDA
MSFT
```

### **Alert Intervals**

Configure in `app/bot_modular.py`:
```python
# 52-week high alerts (every 6 hours)
scheduler.add_job(send_52w_high_alert, 'interval', hours=6)

# Moving average crossovers (every 12 hours)
scheduler.add_job(send_moving_average_alerts, 'interval', hours=12)
```

---

## 💡 **Usage Examples**

### **Telegram Bot Commands**

```
AAPL                    # Brief company info
/quote AAPL            # Detailed quote with metrics
/research TSLA         # Full AI analysis
/add NVDA              # Add to watchlist
/remove MSFT           # Remove from watchlist
/stocks                # List all monitored stocks with company names
/help                  # Show all commands
```

### **Web App Workflow**

1. Enter ticker (e.g., "AAPL")
2. View real-time price, 52-week data, RSI, volatility
3. Check market sentiment in sidebar
4. Ask AI questions: "Should I buy AAPL now?"
5. Analyze interactive charts

---

## 🎨 **Architecture Highlights**

### **Hybrid Data System**
- **Primary**: FMP API v3 with yearHigh/yearLow (paid plan)
- **Fallback**: Yahoo Finance direct API
- **Smart Caching**: Company names auto-cached from FMP quotes (zero extra API calls)
- **Rate Limiting**: Configurable delays, staggered startup

### **Web App Config**
- **Inline Configuration**: `WebConfig` class in app.py reads st.secrets first, then env vars
- **os.getenv Patch**: Intercepts calls from bot's `app/config.py` to read Streamlit secrets
- **Path Detection**: Multi-path search for `app/` folder (/app/app works on HF Docker)

### **Market Sentiment Calculation**
- **VIX Level**: 17-24 neutral (not 20-30)
- **S&P 500 Momentum**: 5-day price change
- **Treasury Yields**: 10-year rate analysis
- **Market Breadth**: Advancing vs declining stocks

---

## 🐛 **Troubleshooting**

### **Web App Shows Mock Data**
**Symptoms:** AAPL shows $270 instead of ~$266

**Solution:**
1. Check Dockerfile includes `COPY app/ ./app/`
2. Verify Container logs show `✅ Added app path: /app/app (services found)`
3. Ensure FMP_API_KEY is set in Streamlit secrets

### **"No module named 'services'"**
**Solution:** Dockerfile missing `COPY app/ ./app/` line. See [market-chat-web/HUGGINGFACE_DEPLOY.md](market-chat-web/HUGGINGFACE_DEPLOY.md)

### **API Rate Limits**
**Solution:** Increase `FMP_DELAY_SECONDS` in .env or reduce alert frequency

---

## 📝 **API Keys Required**

| Service | Required For | Free Tier | Link |
|---------|-------------|-----------|------|
| **Groq** | AI analysis | ✅ Yes | https://console.groq.com/keys |
| **FMP** | Real-time quotes, 52W data | ⚠️ Paid recommended | https://financialmodelingprep.com |
| **Telegram** | Bot functionality | ✅ Yes | https://t.me/BotFather |

---

## 🤝 **Contributing**

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 **Acknowledgments**

- **Financial Modeling Prep** for reliable financial data API
- **Groq** for ultra-fast LLM inference
- **Streamlit** for elegant web app framework
- **Hugging Face** for free hosting

---

## 📧 **Contact**

- **GitHub**: [@joeyflng](https://github.com/joeyflng)
- **Project**: [ds2-capstone-telegram-ai-alerts](https://github.com/joeyflng/ds2-capstone-telegram-ai-alerts)
- **Live Demo**: https://huggingface.co/spaces/starryeyeowl/dsai-2-ai-market-chat

---

**⭐ If you find this project useful, please consider giving it a star on GitHub!**
