"""
Direct Yahoo Finance API provider - bypasses yfinance for reliable data
"""
import requests
import json
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Enhanced rate limiting configuration - AGGRESSIVE SETTINGS
RATE_LIMIT_DELAY = 20.0  # Increased to 20 seconds (very conservative)
MAX_RETRIES = 6  # More retries with longer backoff
CACHE_DURATION = 300  # Cache quotes for 5 minutes (reduce API calls)

# Batch processing configuration
INTER_STOCK_DELAY = 30.0  # Increased to 30 seconds between stocks
BATCH_SIZE = 2  # Process only 2 stocks at a time
BATCH_COOLDOWN = 60.0  # 1 minute cooldown between batches

# Simple in-memory cache
_quote_cache = {}
_cache_timestamps = {}

# Enhanced user agent rotation with more diverse browsers
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
]

_last_request = 0
_session = None


def _get_session():
    """Get reusable session for connection pooling"""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    return _session


def _get_cache_key(symbol: str, request_type: str = 'quote') -> str:
    """Generate cache key for symbol and request type"""
    return f"{symbol.upper()}_{request_type}"


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid"""
    if cache_key not in _cache_timestamps:
        return False
    
    elapsed = time.time() - _cache_timestamps[cache_key]
    return elapsed < CACHE_DURATION


def _get_from_cache(cache_key: str) -> Optional[Dict]:
    """Get data from cache if valid"""
    if _is_cache_valid(cache_key) and cache_key in _quote_cache:
        return _quote_cache[cache_key]
    return None


def _store_in_cache(cache_key: str, data: Dict):
    """Store data in cache with timestamp"""
    _quote_cache[cache_key] = data
    _cache_timestamps[cache_key] = time.time()


def _wait_for_rate_limit():
    """Enhanced rate limiting with jitter to avoid 429 errors"""
    global _last_request
    elapsed = time.time() - _last_request
    if elapsed < RATE_LIMIT_DELAY:
        # Add jitter to avoid synchronized requests
        jitter = random.uniform(0.5, 1.5)
        sleep_time = (RATE_LIMIT_DELAY - elapsed) * jitter
        time.sleep(sleep_time)
    _last_request = time.time()


def _make_yahoo_request(url: str, timeout: int = 15) -> Optional[dict]:
    """Make a request to Yahoo Finance API with enhanced retry logic"""
    
    session = _get_session()
    
    for attempt in range(MAX_RETRIES):
        try:
            _wait_for_rate_limit()
            
            # Rotate user agent for each attempt
            session.headers.update({
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': 'https://finance.yahoo.com/',
                'X-Requested-With': 'XMLHttpRequest'
            })
            
            response = session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Enhanced exponential backoff with jitter
                base_delay = 2 ** attempt
                jitter = random.uniform(0.5, 1.5)
                delay = base_delay * jitter + random.uniform(2, 5)
                print(f"⚠️ Rate limited, waiting {delay:.1f}s (attempt {attempt + 1})")
                time.sleep(delay)
                continue
            elif response.status_code in [403, 404]:
                print(f"⚠️ HTTP {response.status_code} - Skipping retries")
                break
            else:
                print(f"⚠️ HTTP {response.status_code} for {url}")
                
        except Exception as e:
            print(f"⚠️ Request error (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                # Progressive delay with jitter
                delay = (1 + attempt) * random.uniform(1.5, 2.5)
                time.sleep(delay)
    
    return None


def get_yahoo_quote(symbol: str) -> Optional[Dict]:
    """Get real-time quote from Yahoo Finance API with caching"""
    
    # Check cache first
    cache_key = _get_cache_key(symbol, 'quote')
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}'
    
    try:
        data = _make_yahoo_request(url)
        
        if not data or 'chart' not in data:
            return None
            
        chart = data['chart']
        if not chart['result']:
            return None
            
        result = chart['result'][0]
        meta = result['meta']
        
        # Extract quote data
        current_price = meta.get('regularMarketPrice', 0)
        prev_close = meta.get('previousClose', current_price)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        quote_data = {
            'symbol': meta.get('symbol', symbol.upper()),
            'companyName': meta.get('longName', f"{symbol.upper()} Corporation"),
            'price': current_price,
            'change': change,
            'changePercent': change_pct,
            'volume': meta.get('regularMarketVolume', 0),
            'dayHigh': meta.get('regularMarketDayHigh', current_price),
            'dayLow': meta.get('regularMarketDayLow', current_price),
            'week52High': meta.get('fiftyTwoWeekHigh', current_price * 1.2),
            'week52Low': meta.get('fiftyTwoWeekLow', current_price * 0.8),
            'marketCap': meta.get('marketCap'),
            'peRatio': None  # Not available in chart API
        }
        
        # Cache the result to reduce API calls
        _store_in_cache(cache_key, quote_data)
        
        return quote_data
        
    except Exception as e:
        print(f"❌ Error getting Yahoo quote for {symbol}: {e}")
        return None


def get_yahoo_history(symbol: str, period: str = "1y") -> Optional[Tuple[List[float], List[str], List[Dict]]]:
    """Get historical data from Yahoo Finance API with caching"""
    
    # Check cache first (cache for 5 minutes for historical data)
    cache_key = _get_cache_key(symbol, f'history_{period}')
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Convert period to timestamps
    end_time = int(datetime.now().timestamp())
    
    period_map = {
        '1d': 1, '5d': 5, '1mo': 30, '3mo': 90, '6mo': 180,
        '1y': 365, '2y': 730, '5y': 1825, 'max': 3650
    }
    
    days = period_map.get(period, 365)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp())
    
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?period1={start_time}&period2={end_time}&interval=1d'
    
    try:
        data = _make_yahoo_request(url, timeout=15)
        
        if not data or 'chart' not in data:
            return None
            
        chart = data['chart']
        if not chart['result']:
            return None
            
        result = chart['result'][0]
        timestamps = result['timestamp']
        indicators = result['indicators']['quote'][0]
        
        # Extract OHLCV data
        opens = indicators['open']
        highs = indicators['high']
        lows = indicators['low']
        closes = indicators['close']
        volumes = indicators['volume']
        
        # Filter out None values and convert to proper types
        prices = []
        dates = []
        historical_data = []
        
        for i, timestamp in enumerate(timestamps):
            if (closes[i] is not None and opens[i] is not None and 
                highs[i] is not None and lows[i] is not None):
                
                date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                prices.append(float(closes[i]))
                dates.append(date)
                
                historical_data.append({
                    'date': date,
                    'close': float(closes[i]),
                    'open': float(opens[i]),
                    'high': float(highs[i]),
                    'low': float(lows[i]),
                    'volume': int(volumes[i]) if volumes[i] else 0
                })
        
        result = (prices, dates, historical_data)
        
        # Cache the result to reduce API calls
        _store_in_cache(cache_key, result)
        
        return result
        
    except Exception as e:
        print(f"❌ Error getting Yahoo history for {symbol}: {e}")
        return None


def get_multiple_quotes(symbols: List[str], use_delays: bool = True) -> Dict[str, Dict]:
    """
    Get quotes for multiple stocks with intelligent rate limiting
    
    Args:
        symbols: List of stock symbols
        use_delays: Whether to add delays between requests (recommended: True)
    
    Returns:
        Dictionary mapping symbol -> quote data
    """
    results = {}
    
    print(f"📊 Getting quotes for {len(symbols)} stocks...")
    
    for i, symbol in enumerate(symbols):
        print(f"🔄 [{i+1}/{len(symbols)}] Fetching {symbol}...")
        
        try:
            quote = get_yahoo_quote(symbol)
            if quote:
                results[symbol] = quote
                print(f"✅ {symbol}: ${quote['price']:.2f}")
            else:
                print(f"❌ Failed to get {symbol}")
                
        except Exception as e:
            print(f"❌ Error getting {symbol}: {e}")
        
        # Smart inter-stock delay (skip for last stock)
        if use_delays and i < len(symbols) - 1:
            delay = INTER_STOCK_DELAY
            
            # Add extra delay every BATCH_SIZE stocks
            if (i + 1) % BATCH_SIZE == 0:
                delay = BATCH_COOLDOWN
                print(f"⏳ Batch cooldown: {delay}s...")
            else:
                print(f"⏳ Inter-stock delay: {delay}s...")
            
            time.sleep(delay)
    
    print(f"📈 Retrieved {len(results)}/{len(symbols)} quotes successfully")
    return results


def get_quotes_with_smart_delays(symbols: List[str], max_concurrent: int = 3) -> Dict[str, Dict]:
    """
    Get quotes with smart batching and optimal delays
    
    This function is optimized to minimize rate limiting while maintaining speed.
    """
    if len(symbols) <= max_concurrent:
        # For small lists, use simple delays
        return get_multiple_quotes(symbols, use_delays=True)
    
    # For large lists, process in batches
    results = {}
    
    for i in range(0, len(symbols), max_concurrent):
        batch = symbols[i:i + max_concurrent]
        batch_num = (i // max_concurrent) + 1
        total_batches = (len(symbols) + max_concurrent - 1) // max_concurrent
        
        print(f"🔄 Processing batch {batch_num}/{total_batches}: {batch}")
        
        batch_results = get_multiple_quotes(batch, use_delays=True)
        results.update(batch_results)
        
        # Longer delay between batches
        if i + max_concurrent < len(symbols):
            print(f"⏳ Batch cooldown: {BATCH_COOLDOWN}s...")
            time.sleep(BATCH_COOLDOWN)
    
        return results


def get_yahoo_batch_quotes(symbols: List[str]) -> Dict[str, Dict]:
    """Fetch multiple quotes in a single Yahoo request when possible.

    Uses the v7 quote endpoint which supports comma-separated symbols.
    Populates per-symbol cache entries to integrate with existing caching.
    """
    results: Dict[str, Dict] = {}
    if not symbols:
        return results

    # Deduplicate and sanitize symbols
    uniq = []
    seen = set()
    for s in symbols:
        su = s.upper()
        if su not in seen:
            uniq.append(su)
            seen.add(su)

    # Prepare URL
    joined = ",".join(uniq)
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={joined}"

    try:
        data = _make_yahoo_request(url, timeout=20)
        items = []
        if data and 'quoteResponse' in data:
            items = data['quoteResponse'].get('result', [])

        if items:
            for item in items:
                symbol = item.get('symbol')
                if not symbol:
                    continue
                current_price = item.get('regularMarketPrice', 0.0)
                prev_close = item.get('regularMarketPreviousClose', current_price)
                change = (current_price - prev_close) if prev_close is not None else 0.0
                change_pct = (change / prev_close * 100) if prev_close else 0.0

                quote_data = {
                    'symbol': symbol,
                    'companyName': item.get('longName') or item.get('shortName') or symbol,
                    'price': float(current_price) if current_price is not None else 0.0,
                    'change': float(change),
                    'changePercent': float(change_pct),
                    'volume': item.get('regularMarketVolume', 0) or 0,
                    'dayHigh': item.get('regularMarketDayHigh', current_price),
                    'dayLow': item.get('regularMarketDayLow', current_price),
                    'week52High': item.get('fiftyTwoWeekHigh', current_price),
                    'week52Low': item.get('fiftyTwoWeekLow', current_price),
                    'marketCap': item.get('marketCap'),
                    'peRatio': item.get('trailingPE')
                }

                # Cache and store
                cache_key = _get_cache_key(symbol, 'quote')
                _store_in_cache(cache_key, quote_data)
                results[symbol] = quote_data

            return results

        # Fallback: per-symbol queries using chart endpoint logic
        for s in uniq:
            single = get_yahoo_quote(s)
            if single:
                results[s] = single
        return results
    except Exception as e:
        print(f"❌ Error in Yahoo batch quotes: {e}")
        return results


def get_yahoo_company_info(symbol: str) -> Optional[Dict]:
    """
    Get company fundamental data from Yahoo Finance API with rate limiting
    
    Returns company profile, financial metrics, and basic info
    """
    # Check cache first (cache for 5 minutes for company info)
    cache_key = _get_cache_key(symbol, 'company_info')
    cached_data = _get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Use the modules endpoint for more detailed company info
    url = f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol.upper()}?modules=assetProfile,financialData,defaultKeyStatistics,summaryProfile'
    
    try:
        data = _make_yahoo_request(url, timeout=20)
        
        if not data or 'quoteSummary' not in data:
            return None
            
        quote_summary = data['quoteSummary']
        if not quote_summary.get('result'):
            return None
            
        result = quote_summary['result'][0]
        
        # Extract company profile
        asset_profile = result.get('assetProfile', {})
        financial_data = result.get('financialData', {})
        key_stats = result.get('defaultKeyStatistics', {})
        summary_profile = result.get('summaryProfile', {})
        
        company_info = {
            'symbol': symbol.upper(),
            'profile': {
                'companyName': asset_profile.get('longBusinessSummary', {}).get('longName', symbol),
                'sector': asset_profile.get('sector', 'N/A'),
                'industry': asset_profile.get('industry', 'N/A'),
                'description': asset_profile.get('longBusinessSummary', 'N/A'),
                'employees': asset_profile.get('fullTimeEmployees', 0),
                'country': asset_profile.get('country', 'N/A'),
                'website': asset_profile.get('website', 'N/A'),
                'city': asset_profile.get('city', 'N/A'),
                'state': asset_profile.get('state', 'N/A')
            },
            'metrics': {
                'marketCap': financial_data.get('marketCap', {}).get('raw', 0),
                'pe_ratio': key_stats.get('trailingPE', {}).get('raw'),
                'forward_pe': key_stats.get('forwardPE', {}).get('raw'),
                'peg_ratio': key_stats.get('pegRatio', {}).get('raw'),
                'price_to_book': key_stats.get('priceToBook', {}).get('raw'),
                'price_to_sales': key_stats.get('priceToSalesTrailing12Months', {}).get('raw'),
                'enterprise_value': key_stats.get('enterpriseValue', {}).get('raw'),
                'profit_margins': financial_data.get('profitMargins', {}).get('raw'),
                'revenue_growth': financial_data.get('revenueGrowth', {}).get('raw'),
                'return_on_equity': financial_data.get('returnOnEquity', {}).get('raw'),
                'return_on_assets': financial_data.get('returnOnAssets', {}).get('raw'),
                'debt_to_equity': financial_data.get('debtToEquity', {}).get('raw'),
                'current_ratio': financial_data.get('currentRatio', {}).get('raw'),
                'quick_ratio': financial_data.get('quickRatio', {}).get('raw'),
                'gross_margins': financial_data.get('grossMargins', {}).get('raw'),
                'operating_margins': financial_data.get('operatingMargins', {}).get('raw'),
                'ebitda_margins': financial_data.get('ebitdaMargins', {}).get('raw')
            },
            'financial_data': {
                'total_cash': financial_data.get('totalCash', {}).get('raw'),
                'total_debt': financial_data.get('totalDebt', {}).get('raw'),
                'total_revenue': financial_data.get('totalRevenue', {}).get('raw'),
                'free_cash_flow': financial_data.get('freeCashflow', {}).get('raw'),
                'operating_cash_flow': financial_data.get('operatingCashflow', {}).get('raw'),
                'earnings_growth': financial_data.get('earningsGrowth', {}).get('raw'),
                'revenue_per_share': financial_data.get('revenuePerShare', {}).get('raw'),
                'target_high_price': financial_data.get('targetHighPrice', {}).get('raw'),
                'target_low_price': financial_data.get('targetLowPrice', {}).get('raw'),
                'target_mean_price': financial_data.get('targetMeanPrice', {}).get('raw'),
                'recommendation_mean': financial_data.get('recommendationMean', {}).get('raw')
            }
        }
        
        # Cache the result
        _store_in_cache(cache_key, company_info)
        
        return company_info
        
    except Exception as e:
        print(f"❌ Error getting Yahoo company info for {symbol}: {e}")
        return None


def get_yahoo_earnings_calendar(symbol: str) -> Optional[Dict]:
    """
    Get earnings calendar data from Yahoo Finance API with rate limiting
    
    Returns upcoming and historical earnings dates
    Note: Using fallback approach due to 401 errors on quoteSummary endpoint
    """
    # Check cache first (cache for 1 hour for earnings data)
    cache_key = _get_cache_key(symbol, 'earnings')
    
    # Use longer cache for earnings (1 hour = 3600 seconds)
    if cache_key in _cache_timestamps:
        elapsed = time.time() - _cache_timestamps[cache_key]
        if elapsed < 3600 and cache_key in _quote_cache:
            return _quote_cache[cache_key]

    # Try multiple endpoints as fallbacks
    endpoints_to_try = [
        # Primary endpoint (may return 401)
        f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol.upper()}?modules=calendarEvents',
        # Alternative chart endpoint with additional modules
        f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?range=1y&includePrePost=true',
        # Simpler modules that might work
        f'https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol.upper()}?modules=defaultKeyStatistics'
    ]
    
    for i, url in enumerate(endpoints_to_try):
        try:
            data = _make_yahoo_request(url, timeout=15)
            
            if not data:
                continue
                
            # Handle different response formats
            earnings_data = {
                'symbol': symbol.upper(),
                'upcoming_earnings': [],
                'earnings_history': [],
                'source': f'endpoint_{i+1}'
            }
            
            # Try to extract earnings from quoteSummary format
            if 'quoteSummary' in data:
                quote_summary = data['quoteSummary']
                if quote_summary.get('result'):
                    result = quote_summary['result'][0]
                    
                    # Extract calendar events if available
                    calendar_events = result.get('calendarEvents', {})
                    if calendar_events and calendar_events.get('earnings'):
                        earnings = calendar_events['earnings']
                        if earnings.get('earningsDate'):
                            for earnings_date in earnings['earningsDate']:
                                if earnings_date.get('raw'):
                                    earnings_data['upcoming_earnings'].append({
                                        'date': datetime.fromtimestamp(earnings_date['raw']).strftime('%Y-%m-%d'),
                                        'timestamp': earnings_date['raw']
                                    })
                    
                    # Cache successful result and return
                    _quote_cache[cache_key] = earnings_data
                    _cache_timestamps[cache_key] = time.time()
                    return earnings_data
            
            # Try chart format (backup)
            elif 'chart' in data:
                # Chart endpoint doesn't have earnings calendar, but we can return structure
                earnings_data['source'] = 'chart_endpoint'
                _quote_cache[cache_key] = earnings_data
                _cache_timestamps[cache_key] = time.time()
                return earnings_data
                
        except Exception as e:
            if "401" in str(e) or "HTTP 401" in str(e):
                print(f"⚠️ HTTP 401 for {url}")
                continue  # Try next endpoint
            else:
                print(f"⚠️ Error with endpoint {i+1} for {symbol}: {e}")
                continue
    
    # If all endpoints fail, return mock/placeholder data
    print(f"⚠️ All earnings endpoints failed for {symbol}, using fallback data")
    
    # Return basic structure with estimated earnings dates (quarterly)
    from datetime import datetime, timedelta
    import calendar
    
    mock_earnings = {
        'symbol': symbol.upper(),
        'upcoming_earnings': [],
        'earnings_history': [],
        'source': 'mock_fallback'
    }
    
    # Generate estimated quarterly earnings dates (most companies report quarterly)
    current_date = datetime.now()
    quarterly_months = [1, 4, 7, 10]  # Typical earnings months
    
    for month in quarterly_months:
        if month > current_date.month:
            # Next earnings in this year
            next_earnings = datetime(current_date.year, month, 15)  # Mid-month estimate
        else:
            # Next earnings in next year
            next_earnings = datetime(current_date.year + 1, month, 15)
            
        if next_earnings > current_date:
            mock_earnings['upcoming_earnings'].append({
                'date': next_earnings.strftime('%Y-%m-%d'),
                'timestamp': int(next_earnings.timestamp()),
                'estimated': True
            })
            break  # Only add next estimated earnings date
    
    # Cache mock result for shorter duration (30 minutes)
    _quote_cache[cache_key] = mock_earnings
    _cache_timestamps[cache_key] = time.time() - 1800  # Expire in 30 min instead of 1 hour
    
    return mock_earnings


# Test function
if __name__ == "__main__":
    print("Testing Direct Yahoo Finance API...")
    
    # Test single quote
    quote = get_yahoo_quote("AAPL")
    if quote:
        print(f"✅ Quote: {quote['symbol']} ${quote['price']:.2f} ({quote['changePercent']:+.2f}%)")
    
    # Test batch processing
    test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    print(f"\n🧪 Testing batch processing with {len(test_symbols)} stocks...")
    batch_quotes = get_multiple_quotes(test_symbols[:3])  # Test with 3 stocks
    
    print(f"\n📊 Batch Results:")
    for symbol, quote in batch_quotes.items():
        print(f"  {symbol}: ${quote['price']:.2f}")
    
    # Test history
    print(f"\n🧪 Testing historical data...")
    hist = get_yahoo_history("AAPL", "1mo")
    if hist:
        prices, dates, data = hist
        print(f"✅ History: {len(prices)} data points from {dates[0]} to {dates[-1]}")