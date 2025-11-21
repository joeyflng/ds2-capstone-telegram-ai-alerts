"""
Earnings service module for financial market updates using rate-limited Yahoo Finance
"""
# import yfinance as yf  # Replaced with rate-limited yahoo_direct
import json
import os
import time
from datetime import date, timedelta, datetime

# Import hybrid FMP + Yahoo functions for better reliability
try:
    from .fmp_hybrid import get_hybrid_earnings_calendar
    HYBRID_EARNINGS_AVAILABLE = True
except ImportError:
    HYBRID_EARNINGS_AVAILABLE = False
    
# Import rate-limited Yahoo Finance functions as fallback
try:
    from .yahoo_direct import get_yahoo_earnings_calendar, get_yahoo_quote
except ImportError:
    from yahoo_direct import get_yahoo_earnings_calendar, get_yahoo_quote

# Handle config import with fallback
try:
    from config import STOCKS_TO_CHECK, EARNINGS_DAYS_AHEAD
except ImportError:
    try:
        from ..config import STOCKS_TO_CHECK, EARNINGS_DAYS_AHEAD
    except ImportError:
        # Fallback to default stocks if config not available
        STOCKS_TO_CHECK = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        EARNINGS_DAYS_AHEAD = 14

# Handle telegram client import
try:
    from core.telegram_client import send_telegram_message
except ImportError:
    try:
        from ..core.telegram_client import send_telegram_message
    except ImportError:
        # Fallback if telegram not available
        def send_telegram_message(msg):
            print(f"📱 [TELEGRAM]: {msg}")


def get_log(file_log_name):
    """Get log file of processed events"""
    try:
        if os.path.exists(file_log_name):
            return json.load(open(file_log_name, "r", encoding="utf-8"))
        else:
            return []
    except Exception as e:
        print(f"⚠️ Error loading log {file_log_name}: {e}")
        return []


def get_earnings_calendar(days_to_check=7):
    """Get earnings calendar for monitored stocks using hybrid FMP + Yahoo APIs"""
    print(f"Getting earnings calendar for {len(STOCKS_TO_CHECK)} stocks (hybrid FMP + Yahoo)")
    
    all_earnings = []
    today = date.today()
    
    # OPTIMIZATION: Fetch full earnings calendar ONCE instead of per-symbol
    full_calendar = None
    calendar_source = None
    
    if HYBRID_EARNINGS_AVAILABLE:
        try:
            print(f"🔵 Fetching full FMP earnings calendar once for all stocks...")
            from_date = today.strftime('%Y-%m-%d')
            to_date = (today + timedelta(days=days_to_check*2)).strftime('%Y-%m-%d')
            
            from .fmp_hybrid import _make_fmp_request, FMP_ENABLED
            if FMP_ENABLED:
                cal_url = 'https://financialmodelingprep.com/api/v3/earning_calendar'
                full_calendar = _make_fmp_request(cal_url, {'from': from_date, 'to': to_date})
                if full_calendar:
                    calendar_source = 'fmp'
                    print(f"✅ FMP returned {len(full_calendar)} total earnings entries")
                else:
                    print(f"⚠️ FMP returned empty earnings calendar")
        except Exception as e:
            print(f"⚠️ Error fetching FMP earnings calendar: {e}")
    
    for symbol in STOCKS_TO_CHECK:
        try:
            print(f"📊 Checking earnings for {symbol}...")
            
            earnings_data = None
            
            # Use cached full calendar if available
            if full_calendar and calendar_source == 'fmp':
                # Filter for this specific symbol
                symbol_earnings = [e for e in full_calendar if e.get('symbol', '').upper() == symbol.upper()]
                
                if symbol_earnings:
                    earnings_data = {
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
                    print(f"✅ Found {len(symbol_earnings)} FMP earnings entries for {symbol}")
                else:
                    print(f"ℹ️ No FMP earnings for {symbol} in next {days_to_check*2} days")
                    earnings_data = {
                        'symbol': symbol.upper(),
                        'upcoming_earnings': [],
                        'source': 'fmp'
                    }
            
            # Fallback to Yahoo if no FMP data
            if not earnings_data:
                print(f"🔄 Using Yahoo fallback for {symbol}")
                earnings_data = get_yahoo_earnings_calendar(symbol)
            
            if not earnings_data:
                print(f"⚠️ No earnings data found for {symbol}")
                continue
            
            # Process upcoming earnings (standardized format)
            upcoming_earnings = earnings_data.get('upcoming_earnings', [])
            
            for earnings_info in upcoming_earnings:
                earnings_date_str = earnings_info.get('date')
                if earnings_date_str:
                    try:
                        earnings_date = datetime.strptime(earnings_date_str, '%Y-%m-%d').date()
                        date_diff = abs((earnings_date - today).days)
                        
                        print(f"🔍 {symbol}: Earnings on {earnings_date} is {date_diff} days away (threshold: {days_to_check} days)")
                        
                        if date_diff <= days_to_check:
                            earnings_entry = {
                                'symbol': symbol,
                                'date': earnings_date,
                                'days_until': (earnings_date - today).days,
                                'timestamp': earnings_info.get('timestamp'),
                                'eps_estimated': earnings_info.get('eps_estimated'),
                                'source': earnings_data.get('source', 'unknown')
                            }
                            all_earnings.append(earnings_entry)
                            print(f"✅ Found upcoming earnings for {symbol} on {earnings_date} ({date_diff} days away)")
                    except ValueError as e:
                        print(f"⚠️ Error parsing date for {symbol}: {e}")
            
            # No delay needed - we fetched the full calendar once, just filtering per symbol now
                
        except Exception as e:
            print(f"❌ Error getting earnings for {symbol}: {e}")
            continue
    
    # Sort by date
    all_earnings.sort(key=lambda x: x['date'])
    
    return all_earnings


def run_and_notify_earnings_calendar():
    """Run earnings calendar check and send telegram notification if new earnings found"""
    earnings = get_earnings_calendar(days_to_check=EARNINGS_DAYS_AHEAD)
    file_log_name = 'earnings_calendar_log.txt'
    earnings_log = get_log(file_log_name)
    
    for earning in earnings:
        try:
            # Create unique key for this earning event
            earning_key = f"{earning['symbol']}_{earning['date']}_{earning.get('epsActual', 'expected')}"
            
            # Check if we've already alerted about this earning
            if earning_key in earnings_log:
                continue
                
            # Add to log
            earnings_log.append(earning_key)
            
            # Determine timing and create appropriate message
            days_until = earning.get('days_until', 0)
            symbol = earning['symbol']
            date_str = earning['date'].strftime('%B %d, %Y')
            
            # Fetch company name for better display
            try:
                from .data_providers import get_stock_quote
                quote = get_stock_quote(symbol)
                company_name = quote.get('companyName', symbol) if quote else symbol
                stock_display = f"{symbol} ({company_name})" if company_name and company_name != symbol else symbol
            except Exception as e:
                print(f"⚠️ Could not fetch company name for {symbol}: {e}")
                stock_display = symbol
            
            if days_until > 0:
                # Upcoming earnings
                message = f"📈 *EARNINGS ALERT*\n🏢 {stock_display} reports earnings in {days_until} days\n📅 Date: {date_str}"
            elif days_until == 0:
                # Earnings today
                message = f"📈 *EARNINGS TODAY*\n🏢 {stock_display} reports earnings today\n📅 Date: {date_str}"
            else:
                # Earnings in the past (but within check range)
                continue
            
            send_telegram_message(message)
            
            # Save log
            with open(file_log_name, "w", encoding="utf-8") as f:
                json.dump(earnings_log, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            error_msg = f"❌ Error processing {earning.get('symbol', 'Unknown')} earnings: {e}"
            send_telegram_message(error_msg)
            print(error_msg)
            
    return earnings


def test_yahoo_finance_earnings_api(symbol="AAPL"):
    """Test rate-limited Yahoo Finance Earnings API with a single stock"""
    print(f"🧪 Testing rate-limited Yahoo Finance Earnings API for {symbol}")
    
    try:
        # Use rate-limited function instead of direct yfinance
        earnings_data = get_yahoo_earnings_calendar(symbol)
        
        if earnings_data:
            print(f"✅ Success! Retrieved earnings data for {symbol}")
            print(f"\n📊 Earnings Data:")
            
            # Display upcoming earnings
            upcoming = earnings_data.get('upcoming_earnings', [])
            if upcoming:
                print(f"📅 Upcoming Earnings:")
                for earnings in upcoming:
                    print(f"  - Date: {earnings.get('date', 'N/A')}")
            else:
                print("  - No upcoming earnings found")
            
            # Display historical earnings
            history = earnings_data.get('earnings_history', [])
            if history:
                print(f"\n📈 Recent Earnings History:")
                for earnings in history:
                    quarter = earnings.get('quarter', 'N/A')
                    eps_actual = earnings.get('eps_actual', 'N/A')
                    eps_estimate = earnings.get('eps_estimate', 'N/A')
                    surprise = earnings.get('surprise', 'N/A')
                    print(f"  - {quarter}: Actual ${eps_actual}, Est ${eps_estimate}, Surprise {surprise}%")
            else:
                print("  - No earnings history found")
        else:
            print(f"❌ No earnings data returned for {symbol}")
            
    except Exception as e:
        print(f"❌ Test failed for {symbol}: {e}")
        return False
        
    return True


def test_earnings_connectivity():
    """Test earnings service connectivity"""
    print("🧪 Testing earnings service connectivity...")
    return test_yahoo_finance_earnings_api("AAPL")


def run_all_earnings():
    """Run all earnings functions"""
    print("🚀 Running all earnings checks...")
    print("="*50)
    
    # Run earnings calendar check
    try:
        print("\n📈 Processing earnings calendar...")
        run_and_notify_earnings_calendar()
    except Exception as e:
        error_msg = f"❌ Error in earnings: {e}"
        print(error_msg)
        send_telegram_message(error_msg)


# Main execution
if __name__ == "__main__":
    print("🚀 Earnings Service Test")
    print("="*50)
    
    # Test individual functions
    test_earnings_connectivity()
    
    # Run full earnings check
    run_all_earnings()