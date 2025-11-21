"""
Market data utilities for AI Market Chat Companion
Fetches stock data and calculates technical indicators
"""
import sys
import os

# Add app directory to path to access hybrid APIs (HF compatibility)
# Try multiple possible locations for the app folder
possible_app_paths = [
    os.path.join(os.path.dirname(__file__), '../../app'),  # Local: market-chat-web/utils/../../app
    os.path.join(os.path.dirname(__file__), '../app'),     # HF: /app/utils/../app
    '/app/app',                                             # HF container: /app/app (most likely)
    os.path.join(os.getcwd(), 'app'),                      # Current dir: ./app
]

app_path_found = None
for app_path in possible_app_paths:
    abs_path = os.path.abspath(app_path)
    if os.path.exists(abs_path):
        # Check if services folder exists in this path
        services_path = os.path.join(abs_path, 'services')
        if os.path.exists(services_path):
            if abs_path not in sys.path:
                sys.path.insert(0, abs_path)
            app_path_found = abs_path
            print(f"✅ Added app path: {abs_path} (services found)", flush=True)
            break
        else:
            print(f"⚠️ Path exists but no services folder: {abs_path}", flush=True)

if not app_path_found:
    print(f"⚠️ App folder not found in any of these locations:", flush=True)
    for path in possible_app_paths:
        print(f"  - {os.path.abspath(path)} (exists: {os.path.exists(os.path.abspath(path))})", flush=True)
    print(f"Current working directory: {os.getcwd()}", flush=True)
    print(f"__file__ location: {os.path.dirname(os.path.abspath(__file__))}", flush=True)

import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# Use centralized hybrid FMP+Yahoo system with rate limiting
try:
    from services.fmp_hybrid import (
        get_hybrid_stock_quote, get_hybrid_stock_history, get_hybrid_company_fundamentals,
        get_multiple_hybrid_quotes
    )
    from services.data_providers import get_stock_quote, get_multiple_stock_quotes
    from services.market_sentiment import calculate_market_sentiment
    HYBRID_API_AVAILABLE = True
    print("✅ Hybrid FMP+Yahoo APIs loaded successfully", flush=True)
except ImportError as e:
    print(f"⚠️ Hybrid FMP+Yahoo APIs not available, falling back to mock data: {e}", flush=True)
    HYBRID_API_AVAILABLE = False


def _filter_to_requested_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Filter DataFrame to only include data for the requested period"""
    if df.empty:
        return df
    
    try:
        # Calculate the cutoff date based on period
        today = pd.Timestamp.now()
        
        if period == '1d':
            cutoff_date = today - pd.Timedelta(days=1)
        elif period == '5d':
            cutoff_date = today - pd.Timedelta(days=5)
        elif period == '1mo' or period == '30d':
            cutoff_date = today - pd.Timedelta(days=30)
        elif period == '3mo':
            cutoff_date = today - pd.Timedelta(days=90)
        elif period == '6mo':
            cutoff_date = today - pd.Timedelta(days=180)
        elif period == '1y':
            cutoff_date = today - pd.Timedelta(days=365)
        elif period == '2y':
            cutoff_date = today - pd.Timedelta(days=730)
        elif period == '5y':
            cutoff_date = today - pd.Timedelta(days=1825)
        else:
            # For 'max', '10y', 'ytd' or unknown periods, return all data
            return df
        
        # Filter DataFrame to only include dates after cutoff
        filtered_df = df[df.index >= cutoff_date]
        
        return filtered_df
    
    except Exception as e:
        print(f"⚠️ Error filtering data for period {period}: {e}")
        return df


def _convert_yahoo_history_to_df(historical_data: list, prices: list, dates: list) -> pd.DataFrame:
    """Convert yahoo_direct history data to pandas DataFrame format"""
    try:
        if not historical_data:
            return pd.DataFrame()
        
        # Create DataFrame from historical data
        df_data = []
        for item in historical_data:
            df_data.append({
                'Open': item['open'],
                'High': item['high'], 
                'Low': item['low'],
                'Close': item['close'],
                'Volume': item['volume']
            })
        
        df = pd.DataFrame(df_data)
        df.index = pd.to_datetime(dates)
        return df
        
    except Exception as e:
        print(f"Error converting yahoo_direct data: {e}")
        return pd.DataFrame()

# Import Streamlit conditionally for error handling
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def _handle_error(message: str):
    """Handle errors with or without Streamlit context"""
    if STREAMLIT_AVAILABLE:
        try:
            st.error(message)
        except:
            print(f"ERROR: {message}")
    else:
        print(f"ERROR: {message}")


def get_mock_data(ticker: str) -> pd.DataFrame:
    """Generate mock data for testing when real data is unavailable"""
    import numpy as np
    
    # Generate 30 days of mock OHLCV data
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    # Mock realistic price data based on ticker
    base_prices = {
        'AAPL': 270, 'MSFT': 510, 'GOOGL': 275, 'TSLA': 350,
        'AMZN': 180, 'NVDA': 480, 'META': 300, 'NFLX': 450
    }
    
    base_price = base_prices.get(ticker.upper(), 100)
    
    # Generate realistic OHLCV data with some volatility
    np.random.seed(hash(ticker) % 1000)  # Consistent data for same ticker
    
    closes = []
    opens = []
    highs = []
    lows = []
    volumes = []
    
    current_price = base_price
    
    for i in range(30):
        # Random daily change between -3% and +3%
        daily_change = np.random.normal(0, 0.015)  # 1.5% daily volatility
        
        open_price = current_price
        close_price = current_price * (1 + daily_change)
        
        # High and low with some intraday volatility
        intraday_range = abs(daily_change) + np.random.uniform(0.005, 0.02)
        high_price = max(open_price, close_price) * (1 + intraday_range/2)
        low_price = min(open_price, close_price) * (1 - intraday_range/2)
        
        # Volume between 1M and 100M shares
        volume = np.random.uniform(1_000_000, 100_000_000)
        
        opens.append(open_price)
        highs.append(high_price)
        lows.append(low_price)
        closes.append(close_price)
        volumes.append(int(volume))
        
        current_price = close_price
    
    df = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    }, index=dates)
    
    return df


def fetch_prices(ticker: str, period: str = "30d") -> pd.DataFrame:
    """
    Fetch stock price data for given ticker and time period using hybrid FMP+Yahoo system
    
    Args:
        ticker: Stock symbol (e.g., 'AAPL')
        period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        
    Returns:
        pd.DataFrame: OHLCV data
    """
    try:
        if HYBRID_API_AVAILABLE:
            # Use hybrid FMP+Yahoo system with rate limiting
            print(f"📊 [Web App] Getting {period} historical data for {ticker} via Hybrid FMP+Yahoo...")
            history_result = get_hybrid_stock_history(ticker, period=period)
            
            if history_result is not None:
                # Extract data from hybrid result format
                prices = history_result.get('prices', [])
                dates = history_result.get('dates', [])
                historical_data = history_result.get('historical_data', [])
                source = history_result.get('source', 'unknown')
                
                if prices and dates and historical_data:
                    df = _convert_yahoo_history_to_df(historical_data, prices, dates)
                    
                    if not df.empty:
                        # Filter data to requested period if we got too much data
                        df_filtered = _filter_to_requested_period(df, period)
                        
                        print(f"✅ [Web App] Retrieved {len(df)} data points for {ticker} from {source}")
                        if len(df_filtered) != len(df):
                            print(f"📊 [Web App] Filtered to {len(df_filtered)} data points for {period} period")
                        
                        return df_filtered
        
        # Fallback to mock data
        print(f"⚠️ [Web App] Using mock data for {ticker} - hybrid API unavailable or returned no data")
        return get_mock_data(ticker)
        
    except Exception as e:
        print(f"⚠️ [Web App] Error fetching data for {ticker}: {str(e)}, using mock data")
        return get_mock_data(ticker)


def fetch_current_quote(ticker: str) -> Dict:
    """
    Fetch current stock quote using hybrid FMP+Yahoo system
    
    Args:
        ticker: Stock symbol (e.g., 'ARM')
        
    Returns:
        dict: Current quote data with price, change, volume etc.
    """
    try:
        if HYBRID_API_AVAILABLE:
            print(f"📊 [Web App] Getting current quote for {ticker} via Hybrid FMP+Yahoo...")
            quote = get_stock_quote(ticker)
            
            if quote and 'price' in quote:
                print(f"✅ [Web App] Retrieved quote for {ticker}: ${quote['price']:.2f}")
                return quote
        
        # Fallback to mock data
        print(f"⚠️ [Web App] Using mock quote for {ticker}")
        mock_df = get_mock_data(ticker)
        if not mock_df.empty:
            return {
                'symbol': ticker.upper(),
                'price': mock_df['Close'].iloc[-1],
                'change': mock_df['Close'].iloc[-1] - mock_df['Close'].iloc[-2] if len(mock_df) > 1 else 0,
                'change_percent': ((mock_df['Close'].iloc[-1] / mock_df['Close'].iloc[-2]) - 1) * 100 if len(mock_df) > 1 else 0,
                'volume': mock_df['Volume'].iloc[-1],
                'is_mock': True
            }
        
        return {}
        
    except Exception as e:
        print(f"⚠️ [Web App] Error fetching quote for {ticker}: {str(e)}")
        return {}


def fetch_multiple_quotes(tickers: list) -> Dict:
    """
    Fetch multiple stock quotes efficiently using batch processing
    
    Args:
        tickers: List of stock symbols
        
    Returns:
        dict: Dictionary with ticker -> quote data mappings
    """
    try:
        if HYBRID_API_AVAILABLE and len(tickers) > 1:
            print(f"📊 [Web App] Getting batch quotes for {len(tickers)} stocks via Hybrid FMP+Yahoo...")
            quotes = get_multiple_stock_quotes(tickers)
            
            if quotes:
                print(f"✅ [Web App] Retrieved {len(quotes)} quotes via batch processing")
                return quotes
        elif HYBRID_API_AVAILABLE:
            # Single ticker fallback
            quote = fetch_current_quote(tickers[0])
            return {tickers[0]: quote} if quote else {}
        
        # Fallback to individual mock data
        print(f"⚠️ [Web App] Using mock quotes for {len(tickers)} stocks")
        result = {}
        for ticker in tickers:
            mock_df = get_mock_data(ticker)
            if not mock_df.empty:
                result[ticker] = {
                    'symbol': ticker.upper(),
                    'price': mock_df['Close'].iloc[-1],
                    'change': mock_df['Close'].iloc[-1] - mock_df['Close'].iloc[-2] if len(mock_df) > 1 else 0,
                    'change_percent': ((mock_df['Close'].iloc[-1] / mock_df['Close'].iloc[-2]) - 1) * 100 if len(mock_df) > 1 else 0,
                    'volume': mock_df['Volume'].iloc[-1],
                    'is_mock': True
                }
        
        return result
        
    except Exception as e:
        print(f"⚠️ [Web App] Error fetching multiple quotes: {str(e)}")
        return {}


def get_basic_stats(df: pd.DataFrame, df_1y: pd.DataFrame = None) -> Dict:
    """
    Calculate basic price statistics
    
    Args:
        df: OHLCV DataFrame for current period
        df_1y: Optional 1-year DataFrame for 52-week high/low calculation
    
    Returns:
        dict: Basic statistics including current price, change, 52-week high/low, etc.
    """
    if df.empty:
        return {}
    
    try:
        current_price = df['Close'].iloc[-1]
        previous_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        
        daily_change = current_price - previous_price
        daily_change_pct = (daily_change / previous_price) * 100 if previous_price != 0 else 0
        
        # Use 1-year data for 52-week high/low if available, otherwise use provided df
        if df_1y is not None and not df_1y.empty:
            high_52w = df_1y['High'].max()
            low_52w = df_1y['Low'].min()
        else:
            # Fallback to available data period
            high_52w = df['High'].max()
            low_52w = df['Low'].min()
        
        volume_avg = df['Volume'].mean()
        
        return {
            'current_price': current_price,
            'previous_price': previous_price,
            'daily_change': daily_change,
            'daily_change_pct': daily_change_pct,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'volume_avg': volume_avg,
            'data_points': len(df)
        }
    
    except Exception as e:
        _handle_error(f"❌ Error calculating stats: {str(e)}")
        return {}


def compute_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """
    Compute Relative Strength Index (RSI)
    
    Args:
        df: OHLCV DataFrame
        period: RSI period (default 14)
    
    Returns:
        float: Current RSI value (0-100)
    """
    if df.empty or len(df) < period + 1:
        return 50.0  # Neutral RSI
    
    try:
        closes = df['Close']
        delta = closes.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    except Exception as e:
        _handle_error(f"❌ Error calculating RSI: {str(e)}")
        return 50.0


def compute_sma20(df: pd.DataFrame) -> float:
    """
    Compute 20-day Simple Moving Average
    
    Args:
        df: OHLCV DataFrame
    
    Returns:
        float: Current 20-day SMA
    """
    if df.empty or len(df) < 20:
        return df['Close'].iloc[-1] if not df.empty else 0.0
    
    try:
        sma20 = df['Close'].rolling(window=20).mean()
        return sma20.iloc[-1] if not pd.isna(sma20.iloc[-1]) else df['Close'].iloc[-1]
    
    except Exception as e:
        _handle_error(f"❌ Error calculating SMA20: {str(e)}")
        return 0.0


def compute_volatility(df: pd.DataFrame, period: int = 30) -> float:
    """
    Compute Historical Volatility (annualized) to match IBKR standards
    
    Args:
        df: OHLCV DataFrame
        period: Period for volatility calculation (default 30 days)
    
    Returns:
        float: Annualized historical volatility as percentage
    """
    if df.empty or len(df) < 2:
        return 0.0
    
    try:
        # Use the most recent 'period' days
        closes = df['Close'].tail(period) if len(df) > period else df['Close']
        returns = closes.pct_change().dropna()
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate annualized volatility (standard deviation * sqrt(252 trading days))
        daily_volatility = returns.std()
        annualized_volatility = daily_volatility * (252 ** 0.5) * 100
        
        return annualized_volatility if not pd.isna(annualized_volatility) else 0.0
    
    except Exception as e:
        _handle_error(f"❌ Error calculating volatility: {str(e)}")
        return 0.0


def get_trend_signal(current_price: float, sma20: float, rsi: float) -> Tuple[str, str]:
    """
    Determine trend signal based on price vs SMA and RSI
    
    Args:
        current_price: Current stock price
        sma20: 20-day simple moving average
        rsi: RSI value
    
    Returns:
        tuple: (signal, emoji) - ('bullish'/'bearish'/'neutral', '🟢'/'🔴'/'🟡')
    """
    try:
        price_above_sma = current_price > sma20
        rsi_bullish = 30 < rsi < 70  # Not overbought/oversold
        rsi_overbought = rsi > 70
        rsi_oversold = rsi < 30
        
        if price_above_sma and rsi_bullish:
            return "bullish", "🟢"
        elif price_above_sma and rsi_overbought:
            return "overbought", "🟡" 
        elif not price_above_sma and rsi_oversold:
            return "oversold", "🟡"
        elif not price_above_sma:
            return "bearish", "🔴"
        else:
            return "neutral", "🟡"
    
    except Exception:
        return "neutral", "🟡"


def get_company_info(ticker: str) -> Dict:
    """
    Get basic company information using hybrid FMP+Yahoo system
    
    Args:
        ticker: Stock symbol
    
    Returns:
        dict: Company info (name, sector, market_cap, etc.)
    """
    try:
        if HYBRID_API_AVAILABLE:
            # Use hybrid FMP+Yahoo system with rate limiting
            print(f"🏢 [Web App] Getting company info for {ticker} via Hybrid FMP+Yahoo...")
            info = get_hybrid_company_fundamentals(ticker)
            
            if info:
                # Ensure market_cap is always a number, never None
                market_cap = info.get('mktCap', info.get('marketCap', 0))
                if market_cap is None:
                    market_cap = 0
                    
                return {
                    'name': info.get('companyName', info.get('longName', ticker.upper())),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'market_cap': market_cap,
                    'description': info.get('description', info.get('longBusinessSummary', 'No description available'))[:500]
                }
        
        # Fallback for when hybrid API is unavailable
        return {
            'name': ticker.upper(),
            'sector': 'Unknown',
            'industry': 'Unknown', 
            'market_cap': 0,
            'description': 'Hybrid FMP+Yahoo API unavailable - using placeholder data'
        }
    
    except Exception as e:
        return {
            'name': ticker.upper(),
            'sector': 'Unknown',
            'industry': 'Unknown', 
            'market_cap': 0,
            'description': f'Unable to fetch company info: {str(e)}'
        }


def validate_ticker(ticker: str) -> bool:
    """
    Validate if ticker symbol exists and has data using hybrid FMP+Yahoo system
    
    Args:
        ticker: Stock symbol to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if HYBRID_API_AVAILABLE:
            # Use hybrid FMP+Yahoo system for validation
            quote = get_stock_quote(ticker)
            return quote is not None and 'price' in quote
        
        # If hybrid API not available, assume valid for common tickers
        common_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'ARM']
        return ticker.upper() in common_tickers
    
    except Exception:
        return False


# Popular ticker suggestions for the UI
POPULAR_TICKERS = {
    'Tech Giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA'],
    'Semiconductors': ['ARM', 'AMD', 'TSM', 'INTC', 'QCOM'],
    'EV & Clean Energy': ['TSLA', 'NIO', 'RIVN', 'LCID'], 
    'Finance': ['JPM', 'BAC', 'GS', 'MS'],
    'Crypto': ['BTC-USD', 'ETH-USD', 'ADA-USD'],
    'Meme Stocks': ['GME', 'AMC', 'BBBY']
}


def get_fear_greed_index() -> Dict:
    """
    Get Fear and Greed Index using FMP-based market sentiment calculator
    Uses VIX, S&P 500 momentum, treasury yields, and market breadth
    
    Returns:
        dict: Fear and Greed Index data with score, rating, and description
    """
    try:
        if HYBRID_API_AVAILABLE:
            # Use FMP-based sentiment calculator
            sentiment = calculate_market_sentiment()
            
            if 'error' not in sentiment:
                score = sentiment['overall_score']
                interpretation = sentiment['interpretation']
                emoji = sentiment['emoji']
                
                # Get component details for description
                components = sentiment['components']
                description_parts = []
                
                if 'vix' in components:
                    vix_val = components['vix']['value']
                    description_parts.append(f"VIX: {vix_val:.1f}")
                
                if 'sp500_momentum' in components:
                    sp_pos = components['sp500_momentum']['position_pct']
                    description_parts.append(f"S&P at {sp_pos:.0f}% of 52W range")
                
                description = f"{interpretation} - " + ", ".join(description_parts)
                
                return {
                    'score': score,
                    'rating': interpretation,
                    'emoji': emoji,
                    'description': description,
                    'timestamp': sentiment['timestamp'],
                    'source': 'fmp'
                }
        
        # Fallback to calculated version if FMP unavailable
        return get_calculated_fear_greed_index()
        
    except Exception as e:
        print(f"⚠️ [Web App] FMP sentiment error: {e}")
        return get_calculated_fear_greed_index()


def get_calculated_fear_greed_index() -> Dict:
    """
    Calculate a simplified Fear and Greed Index based on market indicators
    FALLBACK METHOD - Used when alternative.me API is unavailable
    
    Returns:
        dict: Calculated Fear and Greed Index data
    """
    # Commented out - kept as fallback for when alternative.me API fails
    # This calculated version uses VIX and SPY to estimate market sentiment
    try:
        # Get market data for major indices
        spy_data = fetch_current_quote('SPY')  # S&P 500 ETF
        vix_data = fetch_current_quote('^VIX')  # VIX volatility index
        
        if not spy_data or not vix_data:
            # Ultimate fallback with neutral score
            return {
                'score': 50,
                'rating': 'Neutral',
                'emoji': '😐',
                'description': 'Market sentiment data unavailable',
                'timestamp': datetime.now().isoformat(),
                'source': 'calculated'
            }
        
        # Simple calculation based on VIX (fear indicator)
        vix_price = vix_data.get('price', 20)
        
        # VIX interpretation (inverted for fear/greed scale):
        # VIX < 12: Extreme Greed
        # VIX 12-20: Greed  
        # VIX 20-30: Neutral/Fear
        # VIX 30-40: Fear
        # VIX > 40: Extreme Fear
        
        if vix_price < 12:
            score = 80  # Extreme Greed
        elif vix_price < 20:
            score = 65  # Greed
        elif vix_price < 30:
            score = 45  # Neutral to Fear
        elif vix_price < 40:
            score = 25  # Fear
        else:
            score = 10  # Extreme Fear
        
        # Add some market momentum factor
        spy_change = spy_data.get('changePercent', 0)
        if spy_change > 1:
            score += 10  # Strong positive momentum
        elif spy_change > 0:
            score += 5   # Positive momentum
        elif spy_change < -2:
            score -= 10  # Strong negative momentum
        elif spy_change < 0:
            score -= 5   # Negative momentum
        
        # Clamp score to 0-100 range
        score = max(0, min(100, score))
        
        rating, emoji, description = _get_fear_greed_rating(score)
        
        return {
            'score': score,
            'rating': rating,
            'emoji': emoji,
            'description': f"{description} (VIX: {vix_price:.1f}, SPY: {spy_change:+.1f}%)",
            'timestamp': datetime.now().isoformat(),
            'source': 'calculated'
        }
        
    except Exception as e:
        print(f"⚠️ [Web App] Error calculating Fear & Greed Index: {e}")
        # Final fallback
        return {
            'score': 50,
            'rating': 'Neutral',
            'emoji': '😐',
            'description': 'Unable to calculate market sentiment',
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback'
        }


def _get_fear_greed_rating(score: float) -> tuple:
    """
    Convert Fear and Greed score to rating, emoji, and description
    
    Args:
        score: Fear and Greed score (0-100)
        
    Returns:
        tuple: (rating, emoji, description)
    """
    if score >= 75:
        return "Extreme Greed", "🤑", "Markets showing extreme greed - potential correction ahead"
    elif score >= 55:
        return "Greed", "😊", "Markets showing greed - bullish sentiment dominates"
    elif score >= 45:
        return "Neutral", "😐", "Markets showing neutral sentiment"
    elif score >= 25:
        return "Fear", "😰", "Markets showing fear - bearish sentiment dominates"
    else:
        return "Extreme Fear", "😱", "Markets showing extreme fear - potential buying opportunity"


def format_price(price: float) -> str:
    """Format price for display"""
    if price >= 1000:
        return f"${price:,.2f}"
    else:
        return f"${price:.2f}"


def format_market_cap(market_cap: float) -> str:
    """Format market cap for display"""
    if market_cap >= 1e12:
        return f"${market_cap/1e12:.2f}T"
    elif market_cap >= 1e9:
        return f"${market_cap/1e9:.2f}B"
    elif market_cap >= 1e6:
        return f"${market_cap/1e6:.2f}M"
    else:
        return f"${market_cap:,.0f}"


def format_volume(volume: float) -> str:
    """Format volume for display"""
    if volume >= 1e9:
        return f"{volume/1e9:.2f}B"
    elif volume >= 1e6:
        return f"{volume/1e6:.2f}M"
    elif volume >= 1e3:
        return f"{volume/1e3:.2f}K"
    else:
        return f"{volume:.0f}"


def format_fear_greed_score(score: float) -> str:
    """Format Fear and Greed score for display"""
    return f"{score:.0f}/100"