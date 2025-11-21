import os
import json
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
FMP_API_KEY = os.getenv("FMP_API_KEY", "")

ALERT_STOCK_INTERVAL = int(os.getenv("ALERT_STOCK_INTERVAL", "3600"))
ALERT_FX_INTERVAL = int(os.getenv("ALERT_FX_INTERVAL", "3600"))
ALERT_EARNINGS_INTERVAL = int(os.getenv("ALERT_EARNINGS_INTERVAL", "86400"))  # Default 24 hours
ALERT_DIVIDEND_INTERVAL = int(os.getenv("ALERT_DIVIDEND_INTERVAL", "86400"))  # Default 24 hours
ALERT_MA_CROSSOVER_INTERVAL = int(os.getenv("ALERT_MA_CROSSOVER_INTERVAL", "1800"))  # Default 30 minutes
ALERT_52_WEEK_HIGH_INTERVAL = int(os.getenv("ALERT_52_WEEK_HIGH_INTERVAL", "900"))   # Default 15 minutes  
ALERT_BUY_DIP_INTERVAL = int(os.getenv("ALERT_BUY_DIP_INTERVAL", "600"))             # Default 10 minutes

# Startup delays (in seconds) - stagger alerts on bot startup
STARTUP_DELAY_MA_CROSSOVER = int(os.getenv("STARTUP_DELAY_MA_CROSSOVER", "20"))
STARTUP_DELAY_STOCK = int(os.getenv("STARTUP_DELAY_STOCK", "40"))
STARTUP_DELAY_52_WEEK_HIGH = int(os.getenv("STARTUP_DELAY_52_WEEK_HIGH", "60"))
STARTUP_DELAY_BUY_DIP = int(os.getenv("STARTUP_DELAY_BUY_DIP", "80"))
STARTUP_DELAY_EARNINGS = int(os.getenv("STARTUP_DELAY_EARNINGS", "100"))
STARTUP_DELAY_DIVIDENDS = int(os.getenv("STARTUP_DELAY_DIVIDENDS", "120"))

# Default stocks and FX from environment variables
DEFAULT_STOCKS = [s.strip() for s in os.getenv("DEFAULT_STOCKS", "AAPL,MSFT,GOOGL").split(",") if s.strip()]
DEFAULT_FX = [s.strip() for s in os.getenv("DEFAULT_FX", "USDSGD=X,EURUSD=X,USDJPY=X").split(",") if s.strip()]

def load_stock_list():
    """Load stock list from file if available, otherwise use default from .env"""
    stock_list_file = os.path.join(os.path.dirname(__file__), "data", "stock_list.txt")
    
    if os.path.exists(stock_list_file):
        try:
            with open(stock_list_file, "r", encoding="utf-8") as f:
                # Read lines and filter out empty lines and comments
                stocks = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        stocks.append(line.upper())  # Ensure uppercase for consistency
                
                if stocks:  # Only use file if it contains valid stocks
                    print(f"Loaded {len(stocks)} stocks from {stock_list_file}")
                    return stocks
                else:
                    print(f"Stock list file {stock_list_file} is empty, using default stocks")
        except Exception as e:
            print(f"Error reading stock list file {stock_list_file}: {e}, using default stocks")
    
    print(f"Using default stocks from .env: {DEFAULT_STOCKS}")
    return DEFAULT_STOCKS

def load_fx_list():
    """Load FX list from file if available, otherwise use default from .env"""
    fx_list_file = os.path.join(os.path.dirname(__file__), "data", "fx_list.txt")
    
    if os.path.exists(fx_list_file):
        try:
            with open(fx_list_file, "r", encoding="utf-8") as f:
                # Read lines and filter out empty lines and comments
                fx_pairs = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        fx_pairs.append(line.upper())  # Ensure uppercase for consistency
                
                if fx_pairs:  # Only use file if it contains valid FX pairs
                    print(f"Loaded {len(fx_pairs)} FX pairs from {fx_list_file}")
                    return fx_pairs
                else:
                    print(f"FX list file {fx_list_file} is empty, using default FX pairs")
        except Exception as e:
            print(f"Error reading FX list file {fx_list_file}: {e}, using default FX pairs")
    
    print(f"Using default FX pairs from .env: {DEFAULT_FX}")
    return DEFAULT_FX

# Load the actual stock and FX lists to use
STOCKS_TO_CHECK = load_stock_list()
FX_TO_CHECK = load_fx_list()

STOCK_THRESHOLD_PCT = float(os.getenv("STOCK_THRESHOLD_PCT", "0.5"))
FX_THRESHOLD_PCT = float(os.getenv("FX_THRESHOLD_PCT", "0.2"))
WEEK_52_HIGH_THRESHOLD_PCT = float(os.getenv("WEEK_52_HIGH_THRESHOLD_PCT", "1.0"))
BUY_DIP_THRESHOLD_PCT = float(os.getenv("BUY_DIP_THRESHOLD_PCT", "10.0"))
EARNINGS_DAYS_AHEAD = int(os.getenv("EARNINGS_DAYS_AHEAD", "14"))
DIVIDEND_DAYS_AHEAD = int(os.getenv("DIVIDEND_DAYS_AHEAD", "30"))
MA_CROSSOVER_DAYS_LOOKBACK = int(os.getenv("MA_CROSSOVER_DAYS_LOOKBACK", "90"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
