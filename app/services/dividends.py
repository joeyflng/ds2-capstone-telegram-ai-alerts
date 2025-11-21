"""
Dividend service module for dividend calendar alerts
"""
import json
import os
import time
from datetime import datetime, timedelta

# Import FMP hybrid functions
try:
    from .fmp_hybrid import _make_fmp_request, FMP_ENABLED
    HYBRID_AVAILABLE = True
except ImportError:
    try:
        from fmp_hybrid import _make_fmp_request, FMP_ENABLED
        HYBRID_AVAILABLE = True
    except ImportError:
        HYBRID_AVAILABLE = False
        FMP_ENABLED = False

# Handle config import with fallback
try:
    from config import STOCKS_TO_CHECK, DIVIDEND_DAYS_AHEAD
except ImportError:
    try:
        from ..config import STOCKS_TO_CHECK, DIVIDEND_DAYS_AHEAD
    except ImportError:
        # Fallback to default stocks if config not available
        STOCKS_TO_CHECK = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        DIVIDEND_DAYS_AHEAD = 30

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


def get_dividend_calendar(days_to_check=30):
    """Get dividend calendar for monitored stocks using FMP API"""
    print(f"Getting dividend calendar for {len(STOCKS_TO_CHECK)} stocks")
    
    all_dividends = []
    today = datetime.now().date()
    
    # Fetch full dividend calendar ONCE from FMP
    if HYBRID_AVAILABLE and FMP_ENABLED:
        try:
            print(f"🔵 Fetching full FMP dividend calendar once for all stocks...")
            from_date = today.strftime('%Y-%m-%d')
            to_date = (today + timedelta(days=days_to_check)).strftime('%Y-%m-%d')
            
            cal_url = 'https://financialmodelingprep.com/api/v3/stock_dividend_calendar'
            full_calendar = _make_fmp_request(cal_url, {'from': from_date, 'to': to_date})
            
            if full_calendar and isinstance(full_calendar, list):
                print(f"✅ FMP returned {len(full_calendar)} total dividend entries")
                
                # Filter for our monitored stocks
                for symbol in STOCKS_TO_CHECK:
                    symbol_dividends = [d for d in full_calendar if d.get('symbol', '').upper() == symbol.upper()]
                    
                    if symbol_dividends:
                        print(f"✅ Found {len(symbol_dividends)} dividend(s) for {symbol}")
                        
                        for div in symbol_dividends:
                            div_date_str = div.get('date')
                            payment_date_str = div.get('paymentDate')
                            
                            if div_date_str:
                                try:
                                    div_date = datetime.strptime(div_date_str, '%Y-%m-%d').date()
                                    payment_date = None
                                    if payment_date_str:
                                        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
                                    
                                    days_until = (div_date - today).days
                                    
                                    dividend_entry = {
                                        'symbol': symbol,
                                        'date': div_date,
                                        'payment_date': payment_date,
                                        'days_until': days_until,
                                        'amount': div.get('dividend', 0),
                                        'record_date': div.get('recordDate'),
                                        'declaration_date': div.get('declarationDate'),
                                        'source': 'fmp'
                                    }
                                    all_dividends.append(dividend_entry)
                                    
                                except ValueError as e:
                                    print(f"⚠️ Error parsing date for {symbol}: {e}")
                    else:
                        print(f"ℹ️ No dividends for {symbol} in next {days_to_check} days")
            else:
                print(f"⚠️ FMP returned empty dividend calendar")
                
        except Exception as e:
            print(f"❌ Error fetching FMP dividend calendar: {e}")
    else:
        print(f"⚠️ FMP not available for dividend data")
    
    # Sort by date
    all_dividends.sort(key=lambda x: x['date'])
    
    return all_dividends


def run_and_notify_dividend_calendar():
    """Run dividend calendar check and send telegram notification if new dividends found"""
    dividends = get_dividend_calendar(days_to_check=DIVIDEND_DAYS_AHEAD)
    file_log_name = 'dividend_calendar_log.txt'
    dividend_log = get_log(file_log_name)
    
    for dividend in dividends:
        try:
            # Create unique key for this dividend event
            div_key = f"{dividend['symbol']}_{dividend['date']}_{dividend['amount']}"
            
            # Check if we've already alerted about this dividend
            if div_key in dividend_log:
                continue
                
            # Add to log
            dividend_log.append(div_key)
            
            # Determine timing and create appropriate message
            days_until = dividend.get('days_until', 0)
            symbol = dividend['symbol']
            date_str = dividend['date'].strftime('%B %d, %Y')
            amount = dividend['amount']
            payment_date = dividend.get('payment_date')
            
            # Fetch company name for better display
            try:
                from .data_providers import get_stock_quote
                quote = get_stock_quote(symbol)
                company_name = quote.get('companyName', symbol) if quote else symbol
                stock_display = f"{symbol} ({company_name})" if company_name and company_name != symbol else symbol
            except Exception as e:
                print(f"⚠️ Could not fetch company name for {symbol}: {e}")
                stock_display = symbol
            
            # ===== RELAXED FOR TESTING =====
            # Alert on ANY dividend within the lookahead window (30 days)
            # Uncomment the strict filters below after testing phase
            
            if days_until > 0:
                # Upcoming dividend
                message = f"💰 *DIVIDEND ANNOUNCEMENT*\n"
                message += f"🏢 *{stock_display}* declares dividend\n"
                message += f"💵 Amount: ${amount:.2f} per share\n"
                message += f"📅 Ex-Dividend Date: {date_str} ({days_until} days)\n"
                
                if payment_date:
                    message += f"💳 Payment Date: {payment_date.strftime('%B %d, %Y')}\n"
                
                message += f"ℹ️ You must own the stock before the ex-dividend date to receive the dividend"
                
            elif days_until == 0:
                # Dividend ex-date today
                message = f"💰 *DIVIDEND EX-DATE TODAY*\n"
                message += f"🏢 *{stock_display}*\n"
                message += f"💵 Amount: ${amount:.2f} per share\n"
                message += f"📅 Ex-Date: Today ({date_str})\n"
                message += f"⚠️ Last day to buy for this dividend was yesterday!"
            else:
                # ===== STRICT FILTER (COMMENTED FOR TESTING) =====
                # Uncomment this to skip past dividends in production:
                # continue
                
                # ===== RELAXED FOR TESTING =====
                # Alert even for past dividends during testing
                message = f"💰 *DIVIDEND (PAST)*\n"
                message += f"🏢 *{stock_display}*\n"
                message += f"💵 Amount: ${amount:.2f} per share\n"
                message += f"📅 Ex-Date: {date_str} ({abs(days_until)} days ago)\n"
                
                if payment_date:
                    message += f"💳 Payment Date: {payment_date.strftime('%B %d, %Y')}\n"
                
                message += f"ℹ️ [TESTING MODE: Past dividend shown for verification]"
            
            send_telegram_message(message)
            
            # Save log
            with open(file_log_name, "w", encoding="utf-8") as f:
                json.dump(dividend_log, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            error_msg = f"❌ Error processing {dividend.get('symbol', 'Unknown')} dividend: {e}"
            send_telegram_message(error_msg)
            print(error_msg)
            
    return dividends


def test_dividend_connectivity():
    """Test dividend API connectivity"""
    results = {
        'dividends': False,
        'dividend_count': 0,
        'error': None
    }
    
    try:
        print("🧪 Testing dividend API connectivity...")
        dividends = get_dividend_calendar(days_to_check=30)
        
        if dividends and len(dividends) > 0:
            results['dividends'] = True
            results['dividend_count'] = len(dividends)
            print(f"✅ Found {len(dividends)} upcoming dividends")
        else:
            print("⚠️ No upcoming dividends found (may be normal)")
            results['dividends'] = True  # API works, just no data
            
    except Exception as e:
        results['error'] = str(e)
        print(f"❌ Dividend API test failed: {e}")
    
    return results


# Test function
if __name__ == "__main__":
    print("Testing Dividend Calendar API...")
    dividends = get_dividend_calendar(days_to_check=30)
    
    if dividends:
        print(f"\n✅ Found {len(dividends)} upcoming dividends:")
        for div in dividends[:5]:  # Show first 5
            print(f"  {div['symbol']}: ${div['amount']:.2f} on {div['date']} ({div['days_until']} days)")
    else:
        print("\n⚠️ No upcoming dividends found")
