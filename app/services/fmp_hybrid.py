"""  
FMP + Yahoo Finance Hybrid Data Provider
Primary: FMP (v3 API) for quotes, fundamentals, earnings, EOD history
Fallback: Yahoo Finance when FMP unavailable or subscription restricted.

2025-11-21 Updates:
- Fixed to use correct FMP v3 API endpoints (/api/v3/quote/{symbol})
- Adaptive disabling after repeated 403 (subscription limits)
- Enhanced logging for debugging API responses
- Company name caching: Auto-extracted from batch quotes (zero extra API calls!)

Company Name Cache Architecture:
- Company names automatically extracted from FMP quote responses
- FMP's batch quote endpoint includes 'name' field - no separate API calls needed
- Names cached in memory as quotes are fetched
- Cache persists for bot lifetime
- When adding a new stock manually: call add_company_name_to_cache(symbol)
- When removing a stock: call remove_company_name_from_cache(symbol)

Performance Benefits:
- Zero extra API calls for company names (extracted from existing quote data)
- No startup delay for preloading
- No rate limiting issues from profile/company info endpoints
- Instant company name availability after first quote fetch

Usage Example:
    # Company names load automatically when fetching quotes:
    quotes = get_multiple_hybrid_quotes(['AAPL', 'TSLA', 'AMZN'])
    # names are now cached for all 3 stocks!
    
    # In alerts - company name is in the quote:
    quote = get_hybrid_stock_quote('AAPL')
    name = quote['companyName']  # Already included!
    
    # Or get from cache directly:
    name = get_cached_company_name('AAPL')
    
    # Manually add a new stock (fetches one quote to get name):
    add_company_name_to_cache('NVDA')
"""
import os
import requests
import time
import random
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Optional, Union

# Import Yahoo fallback functions
from .yahoo_direct import (
    get_yahoo_quote,
    get_yahoo_earnings_calendar,
    get_yahoo_company_info,
    get_yahoo_history,
    get_yahoo_batch_quotes,
)

# Configuration
try:
    # Try relative import first (when running from app/)
    from ..config import FMP_API_KEY
except ImportError:
    try:
        # Try absolute import (when running from root)
        from app.config import FMP_API_KEY
    except ImportError:
        # Fallback to environment variable
        FMP_API_KEY = os.getenv('FMP_API_KEY')

if not FMP_API_KEY:
    # Attempt direct .env load if config import did not populate
    load_dotenv()
    FMP_API_KEY = FMP_API_KEY or os.getenv('FMP_API_KEY')
if not FMP_API_KEY:
    print("⚠️ FMP_API_KEY not found - FMP layer disabled; using Yahoo only")

# Adaptive enable flag / forbidden tracking
FMP_ENABLED = bool(FMP_API_KEY)
_fmp_consecutive_forbidden = 0
_FMP_FORBIDDEN_THRESHOLD = 10  # Increased threshold for paid plans

if FMP_ENABLED:
    print(f"✅ FMP API enabled with key: {FMP_API_KEY[:10]}...")
else:
    print("❌ FMP API disabled - no API key found")

# Rate limiting for FMP
FMP_REQUEST_DELAY = float(os.getenv('FMP_DELAY_SECONDS', '0.5'))  # Configurable delay between FMP requests
_last_fmp_request = 0

# Simple hybrid-layer quote cache (60s)
_hybrid_quote_cache: Dict[str, Dict] = {}
_hybrid_quote_ts: Dict[str, float] = {}
_HYBRID_QUOTE_TTL = 60.0

# Company name cache (persistent for stock list - loaded from batch quotes)
_company_name_cache: Dict[str, str] = {}
_company_name_loaded: bool = False

def preload_company_names_from_quotes(quotes_data: List[Dict]):
    """
    Extract and cache company names from batch quote responses.
    This is called automatically when processing batch quotes - no separate API calls needed!
    """
    global _company_name_cache
    
    for item in quotes_data:
        symbol = item.get('symbol', '').upper()
        name = item.get('name')
        if symbol and name:
            _company_name_cache[symbol] = name

def get_cached_company_name(symbol: str) -> Optional[str]:
    """Get company name from cache. Returns None if not found."""
    return _company_name_cache.get(symbol.upper())

def add_company_name_to_cache(symbol: str, name: str = None):
    """Add or update a company name in the cache. Fetches if name not provided."""
    key = symbol.upper()
    
    if name:
        _company_name_cache[key] = name
        print(f"✅ Added {key}: {name} to cache")
        return name
    
    # Fetch if not provided - get a quote which includes the name
    if FMP_ENABLED:
        try:
            _rate_limit_fmp()
            url = f"https://financialmodelingprep.com/api/v3/quote/{key}?apikey={FMP_API_KEY}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    name = data[0].get('name')
                    if name:
                        _company_name_cache[key] = name
                        print(f"✅ Added {key}: {name} to cache")
                        return name
        except Exception as e:
            print(f"⚠️ FMP quote error for {key}: {e}")
    
    # Fallback to Yahoo
    try:
        info = get_yahoo_company_info(key)
        name = info.get('longName') or info.get('shortName')
        if name:
            _company_name_cache[key] = name
            print(f"✅ Added {key}: {name} to cache (Yahoo)")
            return name
    except Exception as e:
        print(f"⚠️ Yahoo info error for {key}: {e}")
    
    return None

def remove_company_name_from_cache(symbol: str):
    """Remove a company name from the cache (when stock removed from watchlist)."""
    key = symbol.upper()
    if key in _company_name_cache:
        del _company_name_cache[key]
        print(f"🗑️ Removed {key} from company name cache")

def _get_hybrid_cached_quote(symbol: str) -> Optional[Dict]:
    key = symbol.upper()
    ts = _hybrid_quote_ts.get(key)
    if ts and (time.time() - ts) < _HYBRID_QUOTE_TTL:
        return _hybrid_quote_cache.get(key)
    return None

def _set_hybrid_cached_quote(symbol: str, data: Dict):
    key = symbol.upper()
    _hybrid_quote_cache[key] = data
    _hybrid_quote_ts[key] = time.time()

def _fmp_rate_limit():
    """Apply rate limiting for FMP API"""
    global _last_fmp_request
    current_time = time.time()
    time_since_last = current_time - _last_fmp_request
    if time_since_last < FMP_REQUEST_DELAY:
        sleep_time = FMP_REQUEST_DELAY - time_since_last
        time.sleep(sleep_time)
    _last_fmp_request = time.time()

# Alias for backward compatibility
_rate_limit_fmp = _fmp_rate_limit

def get_company_name(symbol: str) -> Optional[str]:
    """
    Get company name from preloaded cache.
    If not in cache (new stock), fetch and add it.
    """
    key = symbol.upper()
    
    # Check cache first
    name = get_cached_company_name(key)
    if name:
        return name
    
    # Not in cache - fetch and add it
    print(f"⚠️ Company name for {key} not in cache, fetching...")
    return add_company_name_to_cache(key)

def _make_fmp_request(url: str, params: dict, timeout: int = 10) -> Optional[Union[Dict, List]]:
    """Make rate-limited request to FMP API with adaptive disabling and exponential backoff."""
    global FMP_ENABLED, _fmp_consecutive_forbidden
    if not FMP_ENABLED or not FMP_API_KEY:
        return None

    max_retries = 3
    base_delay = 0.5
    
    for attempt in range(max_retries + 1):
        _fmp_rate_limit()
        try:
            params_with_key = params.copy()
            params_with_key['apikey'] = FMP_API_KEY
            response = requests.get(url, params=params_with_key, timeout=timeout)
            status = response.status_code
            
            if status == 403:
                _fmp_consecutive_forbidden += 1
                print(f"⚠️ FMP 403 Forbidden ({_fmp_consecutive_forbidden}/{_FMP_FORBIDDEN_THRESHOLD}) for {url}")
                if _fmp_consecutive_forbidden >= _FMP_FORBIDDEN_THRESHOLD:
                    FMP_ENABLED = False
                    print(f"🚫 CRITICAL: Disabling FMP layer due to {_fmp_consecutive_forbidden} consecutive 403s")
                    print(f"🔄 All requests will now use Yahoo Finance (slower, rate limited)")
                return None
                
            if status == 429:
                if attempt < max_retries:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0.1, 0.3)
                    print(f"⚠️ FMP rate limit (429) for {url} - retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    print(f"⚠️ FMP rate limit (429) for {url} - max retries exceeded")
                    return None
                    
            if status == 404:
                print(f"⚠️ FMP 404 Not Found for {url}")
                return None
                
            if status != 200:
                print(f"⚠️ FMP HTTP {status} for {url}")
                if status == 401:
                    print(f"   → FMP API key might be invalid or expired")
                elif status == 403:
                    print(f"   → FMP subscription doesn't have access to this endpoint")
                elif status == 429:
                    print(f"   → FMP rate limit exceeded")
                return None
                
            data = response.json()
            if isinstance(data, dict) and data.get('Error Message'):
                print(f"⚠️ FMP API error message: {data['Error Message']}")
                return None
                
            _fmp_consecutive_forbidden = 0  # reset on success
            return data
            
        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"⚠️ FMP request error for {url}: {e} - retrying in {delay:.1f}s")
                time.sleep(delay)
                continue
            else:
                print(f"⚠️ FMP request error for {url}: {e}")
                return None
    
    return None

def get_hybrid_stock_quote(symbol: str) -> Optional[Dict]:
    """
    Get stock quote - try FMP first, fallback to Yahoo
    
    Returns standardized format:
    {
        'symbol': str,
        'companyName': str,
        'price': float,
        'change': float,
        'changePercent': float,
        'source': 'fmp' | 'yahoo'
    }
    """
    # Return cached if fresh
    cached = _get_hybrid_cached_quote(symbol)
    if cached:
        return cached

    # Try FMP first
    if FMP_ENABLED:
        # FMP v3 quote endpoint
        fmp_url = f"https://financialmodelingprep.com/api/v3/quote/{symbol.upper()}"
        fmp_data = _make_fmp_request(fmp_url, {})
        
        if fmp_data and len(fmp_data) > 0:
            quote = fmp_data[0]
            
            # Fetch company name separately (cached)
            company_name = get_company_name(symbol)
            
            result = {
                'symbol': quote.get('symbol', symbol.upper()),
                'companyName': company_name,
                'price': float(quote.get('price', 0)),
                'change': float(quote.get('change', 0)),
                'changePercent': float(quote.get('changesPercentage', 0)),
                'volume': int(quote.get('volume', 0)),
                'marketCap': quote.get('marketCap'),
                'yearHigh': float(quote.get('yearHigh', 0)),
                'yearLow': float(quote.get('yearLow', 0)),
                'week52High': float(quote.get('yearHigh', 0)),  # Alias for compatibility
                'week52Low': float(quote.get('yearLow', 0)),    # Alias for compatibility
                'source': 'fmp'
            }
            print(f"✅ FMP quote for {symbol}: ${result['price']:.2f}")
            _set_hybrid_cached_quote(symbol, result)
            return result
        else:
            print(f"⚠️ FMP returned no data for {symbol}, falling back to Yahoo")
    else:
        print(f"⚠️ FMP disabled, using Yahoo for {symbol}")
    
    # Fallback to Yahoo
    print(f"🔄 Using Yahoo fallback for {symbol}")
    yahoo_data = get_yahoo_quote(symbol)
    if yahoo_data:
        yahoo_data['source'] = 'yahoo'
        _set_hybrid_cached_quote(symbol, yahoo_data)
        return yahoo_data
    
    return None

def get_hybrid_company_fundamentals(symbol: str) -> Optional[Dict]:
    """
    Get company fundamentals - try FMP first, fallback to Yahoo
    """
    # Try FMP first
    if FMP_ENABLED:
        try:
            # Get company profile (v3 API)
            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol.upper()}"
            profile_data = _make_fmp_request(profile_url, {})
            
            if profile_data and len(profile_data) > 0:
                profile = profile_data[0]
                
                # Get key metrics (v3 API)
                metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol.upper()}"
                metrics_data = _make_fmp_request(metrics_url, {'period': 'annual'})
                
                # Get ratios (v3 API)
                ratios_url = f"https://financialmodelingprep.com/api/v3/ratios/{symbol.upper()}"
                ratios_data = _make_fmp_request(ratios_url, {'period': 'annual'})
                
                return {
                    'symbol': symbol.upper(),
                    'companyName': profile.get('companyName'),
                    'sector': profile.get('sector'),
                    'industry': profile.get('industry'),
                    'marketCap': profile.get('mktCap'),
                    'description': profile.get('description', '')[:500],
                    'metrics': metrics_data[:4] if metrics_data else [],
                    'ratios': ratios_data[:4] if ratios_data else [],
                    'source': 'fmp'
                }
        except Exception as e:
            print(f"⚠️ FMP fundamentals error for {symbol}: {e}")
    
    # Fallback to Yahoo
    print(f"🔄 Using Yahoo fallback for {symbol} fundamentals")
    yahoo_data = get_yahoo_company_info(symbol)
    if yahoo_data:
        # Convert to standardized format
        return {
            'symbol': symbol.upper(),
            'companyName': yahoo_data.get('name'),
            'sector': yahoo_data.get('sector'),
            'industry': yahoo_data.get('industry'),
            'marketCap': yahoo_data.get('market_cap'),
            'description': yahoo_data.get('description', ''),
            'metrics': [],  # Yahoo doesn't provide detailed metrics
            'ratios': [],   # Yahoo doesn't provide detailed ratios
            'source': 'yahoo'
        }
    
    return None

def get_hybrid_earnings_calendar(symbol: str, days_ahead: int = 30) -> Optional[Dict]:
    """
    Get earnings calendar - try FMP first, fallback to Yahoo
    """
    # Try FMP first
    if FMP_ENABLED:
        try:
            print(f"🔵 Trying FMP earnings for {symbol}...")
            today = date.today()
            from_date = today.strftime('%Y-%m-%d')
            to_date = (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            # FMP v3 earnings calendar endpoint
            cal_url = 'https://financialmodelingprep.com/api/v3/earning_calendar'
            earnings_data = _make_fmp_request(cal_url, {'from': from_date, 'to': to_date})
            
            if earnings_data:
                print(f"✅ FMP returned earnings calendar with {len(earnings_data)} total entries")
                # Filter for the specific symbol
                symbol_earnings = [e for e in earnings_data if e.get('symbol', '').upper() == symbol.upper()]
                
                if symbol_earnings:
                    print(f"✅ Found {len(symbol_earnings)} earnings entries for {symbol} from FMP")
                    return {
                        'symbol': symbol.upper(),
                        'upcoming_earnings': [
                            {
                                'date': earning.get('date'),
                                'eps_estimated': earning.get('epsEstimated'),
                                'revenue_estimated': earning.get('revenueEstimated'),
                                'time': earning.get('time')
                            }
                            for earning in symbol_earnings
                        ],
                        'source': 'fmp'
                    }
                else:
                    # FMP returned data but no earnings for this symbol
                    # Return empty result instead of falling back to Yahoo
                    print(f"ℹ️ FMP: No upcoming earnings for {symbol} in next {days_ahead} days")
                    return {
                        'symbol': symbol.upper(),
                        'upcoming_earnings': [],
                        'source': 'fmp'
                    }
            else:
                print(f"⚠️ FMP returned empty/null earnings data - falling back to Yahoo")
        except Exception as e:
            print(f"⚠️ FMP earnings error for {symbol}: {e} - falling back to Yahoo")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️ FMP_ENABLED is False, using Yahoo fallback")
    
    # Only fallback to Yahoo if FMP truly failed (error or disabled), not if no earnings found
    print(f"🔄 Using Yahoo fallback for {symbol} earnings")
    yahoo_data = get_yahoo_earnings_calendar(symbol)
    if yahoo_data:
        yahoo_data['source'] = 'yahoo'
        return yahoo_data
    
    return None

def get_hybrid_stock_history(symbol: str, period: str = "1y") -> Optional[Dict]:
    """
    Get historical data - try FMP first, fallback to Yahoo
    """
    # Try FMP first
    if FMP_ENABLED:
        try:
            # Convert period to FMP format
            period_map = {
                '1d': 1, '5d': 5, '1mo': 30, '3mo': 90, 
                '6mo': 180, '1y': 365, '2y': 730, '5y': 1825
            }
            days = period_map.get(period, 365)
            # FMP v3 historical price endpoint
            hist_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol.upper()}"
            hist_data = _make_fmp_request(hist_url, {})

            historical = None
            if isinstance(hist_data, dict) and hist_data.get('historical'):
                historical = hist_data['historical']
            elif isinstance(hist_data, list) and len(hist_data) > 0 and 'date' in hist_data[0]:
                # Some tiers/endpoints return a bare list instead of wrapped dict
                historical = hist_data

            if historical:
                # FMP returns data in reverse chronological order (newest first)
                # Need to filter to requested period and reverse to chronological order
                from datetime import datetime, timedelta
                
                # Filter to requested days
                if days < len(historical):
                    historical = historical[:days]  # Take most recent N days
                
                # Reverse to chronological order (oldest first)
                historical = historical[::-1]
                
                prices = []
                dates = []
                ohlcv_data = []
                for h in historical:
                    try:
                        prices.append(float(h.get('close', 0)))
                        dates.append(h.get('date'))
                        ohlcv_data.append({
                            'date': h.get('date'),
                            'open': float(h.get('open', 0)),
                            'high': float(h.get('high', 0)),
                            'low': float(h.get('low', 0)),
                            'close': float(h.get('close', 0)),
                            'volume': int(h.get('volume', 0))
                        })
                    except Exception:
                        continue

                if prices and dates:
                    return {
                        'symbol': symbol.upper(),
                        'prices': prices,
                        'dates': dates,
                        'historical_data': ohlcv_data,
                        'source': 'fmp'
                    }
        except Exception as e:
            print(f"⚠️ FMP history error for {symbol}: {e}")
    
    # Fallback to Yahoo
    print(f"🔄 Using Yahoo fallback for {symbol} history")
    yahoo_result = get_yahoo_history(symbol, period)
    if yahoo_result:
        prices, dates, historical_data = yahoo_result
        return {
            'symbol': symbol.upper(),
            'prices': prices,
            'dates': dates, 
            'historical_data': historical_data,
            'source': 'yahoo'
        }
    
    return None

def get_multiple_hybrid_quotes(symbols: List[str], max_fmp_calls: int = 50) -> Dict[str, Dict]:
    """
    Get quotes for multiple symbols with intelligent FMP/Yahoo distribution
    
    Args:
        symbols: List of symbols to fetch
        max_fmp_calls: Maximum FMP calls before switching to Yahoo only (50 for paid plan)
        
    Returns:
        Dict mapping symbol -> quote data
    """
    results: Dict[str, Dict] = {}
    if not symbols:
        return results

    print(f"📊 Getting quotes for {len(symbols)} stocks with hybrid approach...")
    print(f"🔍 FMP_ENABLED status: {FMP_ENABLED}")

    # 1) Serve any fresh cached quotes immediately
    remaining: List[str] = []
    for s in symbols:
        cached = _get_hybrid_cached_quote(s)
        if cached:
            print(f"💾 Using cached data for {s} (source: {cached.get('source', 'unknown')})")
            results[s] = cached
        else:
            remaining.append(s)

    if not remaining:
        print(f"✅ All {len(symbols)} quotes served from cache")
        return results
    
    print(f"📥 Need to fetch {len(remaining)} quotes: {', '.join(remaining)}")

    # 2) Try FMP batch for all remaining stocks (in chunks if needed)
    fmp_served = []
    if FMP_ENABLED:
        try:
            # Process in batches of max_fmp_calls
            for i in range(0, len(remaining), max_fmp_calls):
                batch = remaining[i:i+max_fmp_calls]
                if batch:
                    batch_num = (i // max_fmp_calls) + 1
                    total_batches = (len(remaining) + max_fmp_calls - 1) // max_fmp_calls
                    print(f"🔵 FMP batch {batch_num}/{total_batches}: {len(batch)} stocks: {', '.join(batch)}")
                    
                    # FMP v3 supports comma-separated symbols in URL path
                    joined = ",".join([s.upper() for s in batch])
                    fmp_url = f"https://financialmodelingprep.com/api/v3/quote/{joined}"
                    data = _make_fmp_request(fmp_url, {})
                    
                    if data is None:
                        print(f"❌ FMP batch {batch_num} returned None (API error)")
                        # Continue to next batch instead of failing completely
                        continue
                    elif not isinstance(data, list):
                        print(f"❌ FMP batch {batch_num} returned non-list data: {type(data)}")
                        continue
                    elif len(data) == 0:
                        print(f"❌ FMP batch {batch_num} returned empty list")
                        continue
                    else:
                        print(f"✅ FMP batch {batch_num} returned {len(data)} quotes")
                    
                    if isinstance(data, list) and data:
                        for item in data:
                            sym = item.get('symbol')
                            if not sym:
                                continue
                            
                            # Extract company name from the quote response itself
                            company_name = item.get('name', None)
                            
                            # Cache the company name automatically
                            if company_name:
                                _company_name_cache[sym.upper()] = company_name
                            
                            standardized = {
                                'symbol': sym,
                                'companyName': company_name,
                                'price': float(item.get('price', 0)),
                                'change': float(item.get('change', 0)),
                                'changePercent': float(item.get('changesPercentage', 0)),
                                'volume': int(item.get('volume', 0)),
                                'marketCap': item.get('marketCap'),
                                'yearHigh': float(item.get('yearHigh', 0)),
                                'yearLow': float(item.get('yearLow', 0)),
                                'week52High': float(item.get('yearHigh', 0)),  # Alias for compatibility
                                'week52Low': float(item.get('yearLow', 0)),    # Alias for compatibility
                                'source': 'fmp'
                            }
                            results[sym] = standardized
                            _set_hybrid_cached_quote(sym, standardized)
                            fmp_served.append(sym)
                            print(f"✅ FMP served {sym}: ${standardized['price']:.2f}")
        except Exception as e:
            print(f"⚠️ FMP batch error: {e}")
    else:
        print(f"⚠️ FMP is disabled, skipping FMP batch fetch")

    # 3) Yahoo batch ONLY for stocks that FMP failed to serve
    yahoo_symbols = [s for s in remaining if s.upper() not in set(fmp_served)]
    if yahoo_symbols:
        print(f"🟡 FMP couldn't serve {len(yahoo_symbols)} stocks, falling back to Yahoo: {', '.join(yahoo_symbols)}")
        try:
            yahoo_map = get_yahoo_batch_quotes(yahoo_symbols)
            for sym, q in yahoo_map.items():
                q['source'] = 'yahoo'
                results[sym] = q
                _set_hybrid_cached_quote(sym, q)
        except Exception as e:
            print(f"⚠️ Yahoo batch error: {e}")

    # Summary
    fmp_count = sum(1 for q in results.values() if q.get('source') == 'fmp')
    yahoo_count = sum(1 for q in results.values() if q.get('source') == 'yahoo')
    print(f"📈 Retrieved {len(results)}/{len(symbols)} quotes | FMP: {fmp_count}, Yahoo: {yahoo_count}")
    return results

# Test function
if __name__ == "__main__":
    print("🧪 Testing FMP + Yahoo Hybrid System...")
    
    # Test single quote
    print("\n📊 Testing hybrid quote for AAPL...")
    quote = get_hybrid_stock_quote("AAPL")
    if quote:
        print(f"✅ {quote['symbol']}: ${quote['price']:.2f} ({quote['source']})")
    
    # Test multiple quotes
    print("\n📊 Testing batch quotes...")
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    batch_quotes = get_multiple_hybrid_quotes(test_symbols, max_fmp_calls=2)
    
    for symbol, quote in batch_quotes.items():
        print(f"  {symbol}: ${quote['price']:.2f} ({quote['source']})")