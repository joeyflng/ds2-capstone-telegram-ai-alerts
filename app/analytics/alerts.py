"""
Alert system module for stock monitoring and notifications
"""
import json
import pandas as pd
import os
from config import STOCKS_TO_CHECK
from core.telegram_client import send_telegram_message, send_telegram_photo
from services.data_providers import get_stock_quote, get_historical_prices, get_stock_interval_data, get_multiple_stock_quotes
from analytics.charts import create_ma_crossover_chart


def get_stock_display_name(quote_data):
    """Get formatted stock display name with company name if available"""
    symbol = quote_data.get('symbol', '').upper()
    company_name = quote_data.get('companyName', '').strip()
    
    if company_name and company_name != symbol:
        return f"{symbol} ({company_name})"
    return symbol


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


def calculate_sma(prices, period):
    """Calculate Simple Moving Average for given period"""
    if len(prices) < period:
        return []
    
    sma_values = []
    for i in range(period - 1, len(prices)):
        avg = sum(prices[i - period + 1:i + 1]) / period
        sma_values.append(avg)
    
    return sma_values


def detect_ma_crossovers(data, short_window=50, long_window=200):
    """Detect moving average crossovers in historical data"""
    # Calculate moving averages
    data['MA_Short'] = data['Close'].rolling(window=short_window).mean()
    data['MA_Long'] = data['Close'].rolling(window=long_window).mean()
    
    # Create signal: 1 when short MA > long MA, 0 otherwise
    signals = (data['MA_Short'] > data['MA_Long']).astype(int)
    
    # Find crossover points by looking at signal changes
    crossovers = signals.diff()
    
    # Golden Cross: signal changes from 0 to 1 (crossover = 1)
    golden_crosses = data[crossovers == 1].copy()
    
    # Death Cross: signal changes from 1 to 0 (crossover = -1)  
    death_crosses = data[crossovers == -1].copy()
    
    return golden_crosses, death_crosses, signals


# ============================================================================
# BUY DIP ALERTS
# ============================================================================

def check_and_notify_buy_dip_opportunities(dip_threshold_pct=10.0):
    """
    Check stocks for buy dip opportunities when they've dropped significantly from 52-week highs
    """
    buy_dip_log_name = 'buy_dip_log.txt'
    dip_log = get_log(buy_dip_log_name)
    
    # Use batch quote function to reduce API calls
    print(f"📊 Getting quotes for {len(STOCKS_TO_CHECK)} stocks (buy dip check)...")
    quotes = get_multiple_stock_quotes(STOCKS_TO_CHECK, use_smart_delays=True)
    
    for stock in STOCKS_TO_CHECK:
        try:
            quote = quotes.get(stock) or quotes.get(stock.upper())
            if not quote:
                print(f"⚠️ No quote data for {stock}")
                continue
                
            current_price = quote.get('price')
            year_high = quote.get('week52High') or quote.get('yearHigh')
            year_low = quote.get('week52Low') or quote.get('yearLow')
            symbol = quote.get('symbol', stock)
            name = quote.get('companyName', symbol)
            
            if current_price and year_high:
                # Calculate drop from 52-week high
                drop_from_high = ((year_high - current_price) / year_high) * 100
                
                print(f"🔍 {symbol}: Price=${current_price:.2f}, 52W High=${year_high:.2f}, Drop={drop_from_high:.1f}% (threshold={dip_threshold_pct}%)")
                
                # Check if stock has dropped significantly from 52-week high (buy opportunity)
                if drop_from_high >= dip_threshold_pct:
                    
                    # Create unique key for dip alert
                    dip_alert_key = f"{symbol}_dip_{current_price:.2f}_{year_high:.2f}"
                    
                    # Only alert if we haven't already sent a dip alert for this price level
                    if dip_alert_key not in dip_log:
                        dip_log.append(dip_alert_key)
                        
                        # Calculate potential upside back to 52-week high
                        potential_upside = ((year_high - current_price) / current_price) * 100
                        
                        # Calculate distance from 52-week low for context
                        if year_low:
                            pct_from_low = ((current_price - year_low) / year_low) * 100
                        else:
                            pct_from_low = 0
                        
                        message = (f"💎 *BUY THE DIP OPPORTUNITY!* 💎\n"
                                 f"📊 *{symbol}* ({name})\n"
                                 f"💰 Current Price: ${current_price:.2f}\n"
                                 f"📊 52-Week High: ${year_high:.2f}\n"
                                 f"📉 Drop from High: {drop_from_high:.1f}%\n"
                                 f"🚀 Potential Upside: {potential_upside:.1f}%\n"
                                 f"📈 Above 52W Low: {pct_from_low:.1f}%\n"
                                 f"🛒 Consider dollar-cost averaging!")
                        
                        print(f"💎 Buy dip alert for {symbol}: {drop_from_high:.1f}% drop from high")
                        send_telegram_message(message)
                        
                        # Save the dip log
                        with open(buy_dip_log_name, "w", encoding="utf-8") as f:
                            json.dump(dip_log, f, ensure_ascii=False, indent=2)
                            
        except Exception as e:
            print(f"❌ Error checking buy dip for {stock}: {e}")
            send_telegram_message(f"Error checking buy dip for {stock}: {e}")


# ============================================================================
# 52-WEEK HIGH ALERTS
# ============================================================================

def check_and_notify_52_week_highs(threshold_pct=0.5):
    """
    Check stocks for 52-week high alerts:
    1. New 52-week highs
    2. Approaching 52-week highs 
    3. Watch zone alerts (5-15% below high)
    """
    file_log_name = '52_week_high_log.txt'
    high_log = get_log(file_log_name)
    
    # Use batch quote function to reduce API calls
    print(f"📊 Getting quotes for {len(STOCKS_TO_CHECK)} stocks (52-week high check)...")
    quotes = get_multiple_stock_quotes(STOCKS_TO_CHECK, use_smart_delays=True)
    
    for stock in STOCKS_TO_CHECK:
        try:
            quote = quotes.get(stock) or quotes.get(stock.upper())
            if not quote:
                print(f"⚠️ No quote data for {stock}")
                continue
                
            current_price = quote.get('price')
            year_high = quote.get('week52High') or quote.get('yearHigh')
            symbol = quote.get('symbol', stock)
            name = quote.get('companyName', symbol)
            
            if current_price and year_high:
                # Calculate how close we are to 52-week high
                pct_from_high = ((current_price - year_high) / year_high) * 100
                
                # 1. CHECK FOR 52-WEEK HIGH ALERTS
                # Create a unique key for this alert to avoid duplicates
                alert_key = f"{symbol}_{year_high}_{current_price:.2f}"
                
                # Check if we're at or very close to 52-week high
                if pct_from_high >= -threshold_pct:  # Within threshold_pct of 52-week high
                    
                    # Check if we've already sent an alert for this level
                    if alert_key not in high_log:
                        high_log.append(alert_key)
                        
                        if pct_from_high >= 0:
                            # New 52-week high!
                            message = (f"🔥 *NEW 52-WEEK HIGH!* 🔥\n"
                                     f"📈 *{symbol}* ({name})\n"
                                     f"💰 Current Price: ${current_price:.2f}\n"
                                     f"📊 Previous High: ${year_high:.2f}\n"
                                     f"🚀 New High by: {pct_from_high:.2f}%\n"
                                     f"📅 Time to consider taking profits!")
                        else:
                            # Very close to 52-week high
                            message = (f"🎯 *APPROACHING 52-WEEK HIGH!* 🎯\n"
                                     f"📊 *{symbol}* ({name})\n"
                                     f"💰 Current Price: ${current_price:.2f}\n"
                                     f"📊 52-Week High: ${year_high:.2f}\n"
                                     f"📏 Distance: {abs(pct_from_high):.2f}% below high\n"
                                     f"⚡ Potential breakout opportunity!")
                        
                        print(f"🔥 52-week high alert for {symbol}: {pct_from_high:.2f}% from high")
                        send_telegram_message(message)
                        
                        # Save the log
                        with open(file_log_name, "w", encoding="utf-8") as f:
                            json.dump(high_log, f, ensure_ascii=False, indent=2)
                
                # 2. CHECK FOR NEAR 52-WEEK HIGH (5-15% range for monitoring)
                elif -15.0 <= pct_from_high <= -5.0:
                    # Stock is in the "watch zone" - not too far from highs but not at threshold yet
                    near_high_key = f"{symbol}_near_high_{int(abs(pct_from_high))}"
                    
                    # Send less frequent alerts for this zone (different key structure)
                    if near_high_key not in high_log:
                        high_log.append(near_high_key)
                        
                        message = (f"👀 *WATCH ZONE ALERT!* 👀\n"
                                 f"📊 *{symbol}* ({name})\n"
                                 f"💰 Current Price: ${current_price:.2f}\n"
                                 f"📈 52-Week High: ${year_high:.2f}\n"
                                 f"📏 Distance: {abs(pct_from_high):.1f}% below high\n"
                                 f"🎯 Monitor for potential breakout!")
                        
                        print(f"👀 Watch zone alert for {symbol}: {abs(pct_from_high):.1f}% from high")
                        send_telegram_message(message)
                        
                        # Save the log
                        with open(file_log_name, "w", encoding="utf-8") as f:
                            json.dump(high_log, f, ensure_ascii=False, indent=2)
                            
        except Exception as e:
            print(f"❌ Error checking 52-week high for {stock}: {e}")
            send_telegram_message(f"Error checking 52-week high for {stock}: {e}")


# ============================================================================
# MOVING AVERAGE CROSSOVER ALERTS
# ============================================================================

def check_moving_average_crossover(symbol, short_period=50, long_period=200, lookback_days=7):
    """Check for moving average crossovers (Golden Cross / Death Cross) with enhanced detection
    
    Args:
        symbol: Stock symbol
        short_period: Short MA period (default 50)
        long_period: Long MA period (default 200)
        lookback_days: Only alert on crossovers within this many days (default 7 to avoid old data)
    """
    import pandas as pd
    
    # Use 5 years of data like the notebook for proper MA analysis
    prices, dates, historical_data = get_historical_prices(symbol, period="5y")
    
    if len(prices) < long_period:
        print(f"⚠️  Insufficient data for {symbol}: got {len(prices)}, need {long_period}")
        return None
    
    # Convert to DataFrame for enhanced pandas-based analysis (like working manual test)
    data = pd.DataFrame(historical_data)
    data['Date'] = pd.to_datetime(data['date'])
    data.set_index('Date', inplace=True)
    
    # Rename columns to match enhanced format
    data = data.rename(columns={
        'close': 'Close',
        'open': 'Open', 
        'high': 'High',
        'low': 'Low',
        'volume': 'Volume'
    })
    
    # Calculate MAs using pandas (more robust than manual calculation)
    data[f'MA_{short_period}'] = data['Close'].rolling(window=short_period).mean()
    data[f'MA_{long_period}'] = data['Close'].rolling(window=long_period).mean()
    
    # Enhanced crossover detection using pandas (like working manual test)
    short_ma = data[f'MA_{short_period}']
    long_ma = data[f'MA_{long_period}']
    
    # Create signals: 1 when short MA > long MA, 0 otherwise
    signals = (short_ma > long_ma).astype(int)
    
    # Find crossover points by looking at signal changes
    crossovers = signals.diff()
    
    # Golden Cross: signal changes from 0 to 1 (crossover = 1)
    golden_crosses = data[crossovers == 1]
    
    # Death Cross: signal changes from 1 to 0 (crossover = -1)  
    death_crosses = data[crossovers == -1]
    
    # Check for recent crossovers within lookback period (like enhanced manual test)
    # Use today's date, not the last date in historical data (which might be old)
    from datetime import datetime, timedelta
    today = pd.Timestamp(datetime.now().date())
    recent_date = today - pd.Timedelta(days=lookback_days)
    
    print(f"🔍 {symbol}: Checking for crossovers since {recent_date.strftime('%Y-%m-%d')} (last {lookback_days} days)")
    print(f"🔍 {symbol}: Total golden crosses in 5y data: {len(golden_crosses)}")
    print(f"🔍 {symbol}: Total death crosses in 5y data: {len(death_crosses)}")
    
    recent_golden = golden_crosses[golden_crosses.index >= recent_date]
    recent_death = death_crosses[death_crosses.index >= recent_date]
    
    print(f"🔍 {symbol}: Recent golden crosses (last {lookback_days}d): {len(recent_golden)}")
    print(f"🔍 {symbol}: Recent death crosses (last {lookback_days}d): {len(recent_death)}")
    
    crossover_type = None
    crossover_date = None
    days_since = None
    
    if len(recent_golden) > 0:
        crossover_type = "golden_cross"
        crossover_date = recent_golden.index[-1]
        days_since = (data.index[-1] - crossover_date).days
        print(f"✅ {symbol}: Found golden cross on {crossover_date.strftime('%Y-%m-%d')} ({days_since} days ago)")
    elif len(recent_death) > 0:
        crossover_type = "death_cross" 
        crossover_date = recent_death.index[-1]
        days_since = (data.index[-1] - crossover_date).days
        print(f"✅ {symbol}: Found death cross on {crossover_date.strftime('%Y-%m-%d')} ({days_since} days ago)")
    else:
        print(f"ℹ️ {symbol}: No crossovers found in last {lookback_days} days")
    
    return {
        'symbol': symbol,
        'current_price': data['Close'].iloc[-1],
        'current_short_ma': data[f'MA_{short_period}'].iloc[-1],
        'current_long_ma': data[f'MA_{long_period}'].iloc[-1],
        'crossover_type': crossover_type,
        'crossover_date': crossover_date.strftime('%Y-%m-%d') if crossover_date else None,
        'days_since_crossover': days_since,
        'short_period': short_period,
        'long_period': long_period,
        'latest_date': dates[-1] if dates else None,
        'total_golden_crosses': len(golden_crosses),
        'total_death_crosses': len(death_crosses)
    }


def check_and_notify_ma_crossovers(short_period=50, long_period=200, max_days_old=90):
    """Check for MA crossovers across all monitored stocks
    
    Args:
        short_period: Short MA period (default 50)
        long_period: Long MA period (default 200)
        max_days_old: Maximum age of crossover to alert on (default 90 days / ~3 months)
    """
    file_log_name = 'ma_crossover_log.txt'
    crossover_log = get_log(file_log_name)
    
    for stock in STOCKS_TO_CHECK:
        try:
            result = check_moving_average_crossover(stock, short_period, long_period, lookback_days=max_days_old)
            
            if result and result['crossover_type']:
                # Skip if crossover is older than max_days_old (prevents alerting on old data when adding new stocks)
                if result['days_since_crossover'] > max_days_old:
                    print(f"ℹ️ Skipping old crossover for {stock}: {result['crossover_date']} ({result['days_since_crossover']} days ago)")
                    continue
                
                # Create unique key to avoid duplicate alerts using the actual crossover date
                alert_key = f"{stock}_{result['crossover_type']}_{result['crossover_date']}"
                
                if alert_key not in crossover_log:
                    crossover_log.append(alert_key)
                    
                    # Fetch company name
                    try:
                        quote = get_stock_quote(stock)
                        company_name = quote.get('companyName', stock) if quote else stock
                        stock_display = f"{stock} ({company_name})" if company_name and company_name != stock else stock
                    except:
                        stock_display = stock
                    
                    # Enhanced alert message with crossover date and days since
                    days_ago = f" ({result['days_since_crossover']} days ago)" if result['days_since_crossover'] > 0 else ""
                    
                    if result['crossover_type'] == 'golden_cross':
                        message = (f"🌟 *GOLDEN CROSS!* 🌟\n"
                                 f"📈 *{stock_display}* - Bullish Signal!\n"
                                 f"💰 Current Price: ${result['current_price']:.2f}\n"
                                 f"📊 {short_period}-day MA: ${result['current_short_ma']:.2f}\n"
                                 f"📈 {long_period}-day MA: ${result['current_long_ma']:.2f}\n"
                                 f"🚀 The {short_period}-day MA crossed ABOVE the {long_period}-day MA!\n"
                                 f"📅 Crossover Date: {result['crossover_date']}{days_ago}")
                    else:  # death_cross
                        message = (f"💀 *DEATH CROSS!* 💀\n"
                                 f"📉 *{stock_display}* - Bearish Signal!\n"
                                 f"💰 Current Price: ${result['current_price']:.2f}\n"
                                 f"📊 {short_period}-day MA: ${result['current_short_ma']:.2f}\n"
                                 f"📉 {long_period}-day MA: ${result['current_long_ma']:.2f}\n"
                                 f"⚠️  The {short_period}-day MA crossed BELOW the {long_period}-day MA!\n"
                                 f"📅 Crossover Date: {result['crossover_date']}{days_ago}")
                    
                    print(f"🔔 MA Crossover alert for {stock}: {result['crossover_type']}")
                    
                    # Generate chart first, then send text + chart together
                    chart_path = None
                    try:
                        # Get full data for chart creation - use same 5y period as detection
                        prices, dates, historical_data_list = get_historical_prices(stock, period="5y")
                        if len(prices) >= 200:
                            # Create DataFrame with MAs
                            chart_data = pd.DataFrame(historical_data_list)
                            chart_data['Date'] = pd.to_datetime(chart_data['date'])
                            chart_data.set_index('Date', inplace=True)
                            chart_data = chart_data.rename(columns={
                                'close': 'Close', 'open': 'Open', 'high': 'High', 'low': 'Low', 'volume': 'Volume'
                            })
                            # Use the actual MA periods from the detection
                            short_period = result['short_period']
                            long_period = result['long_period']
                            chart_data[f'MA_{short_period}'] = chart_data['Close'].rolling(window=short_period).mean()
                            chart_data[f'MA_{long_period}'] = chart_data['Close'].rolling(window=long_period).mean()
                            
                            # Create chart
                            chart_path = create_ma_crossover_chart(stock, chart_data, result['crossover_type'], result['crossover_date'])
                    except Exception as chart_error:
                        print(f"⚠️ Could not create chart for {stock}: {chart_error}")
                    
                    # Send text message and chart together
                    send_telegram_message(message)
                    if chart_path:
                        chart_caption = f"📊 *{stock} {result['crossover_type'].replace('_', ' ').title()} Chart*"
                        send_telegram_photo(chart_path, chart_caption)
                        # Clean up
                        try:
                            os.remove(chart_path)
                        except:
                            pass
                    
                    # Save the log
                    with open(file_log_name, "w", encoding="utf-8") as f:
                        json.dump(crossover_log, f, ensure_ascii=False, indent=2)
                        
        except Exception as e:
            print(f"❌ Error checking MA crossover for {stock}: {e}")
            send_telegram_message(f"Error checking MA crossover for {stock}: {e}")


# ============================================================================
# INTRADAY PRICE ALERTS
# ============================================================================

def run_and_notify_stock_interval(threshold_pct=0.5):
    """Run stock interval check and send telegram notification if threshold is met"""
    file_log_name = 'stock_prices_log.txt'
    prices_log = get_log(file_log_name)
    
    # Use batch quote function to reduce API calls
    print(f"📊 Getting interval data for {len(STOCKS_TO_CHECK)} stocks...")
    quotes = get_multiple_stock_quotes(STOCKS_TO_CHECK, use_smart_delays=True)
    
    for stock in STOCKS_TO_CHECK:
        try:
            # Get quote from batch results
            quote = quotes.get(stock) or quotes.get(stock.upper())
            if not quote:
                print(f"⚠️ No quote data available for {stock}")
                continue
                
            # Convert quote to interval data format
            from datetime import datetime
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            current_price = quote['price']
            change = quote.get('change', 0)
            change_percent = quote.get('changePercent', 0)
            
            # Calculate previous close from current price and change
            prev_close = current_price - change if change else current_price
            
            # Create data structure compatible with existing logic
            data = [{
                'symbol': quote['symbol'],
                'open': prev_close,
                'close': current_price,
                'date': current_time,
                'change': change,
                'changePercent': change_percent
            }]
            
            if data is not None and len(data) > 0:
                # Handle pandas DataFrame from yfinance (legacy support)
                if hasattr(data, 'iloc'):
                    latest_row = data.iloc[-1]
                    latest_price = {
                        'symbol': stock,
                        'open': latest_row['Open'],
                        'close': latest_row['Close'],
                        'date': str(data.index[-1])
                    }
                else:
                    # Handle list/dict format from hybrid data provider
                    if isinstance(data, list):
                        latest_price = data[0]
                    else:
                        latest_price = data
                    
                    # Ensure required fields exist
                    if 'symbol' not in latest_price:
                        latest_price['symbol'] = stock
                    
                    # For hybrid data, we use current price for both open/close
                    # since quotes don't have separate open/close for current moment
                    current_price = latest_price.get('close', latest_price.get('price', 0))
                    open_price = latest_price.get('open', current_price)
                    
                    # Use change percentage from quote if available
                    if 'changePercent' in latest_price and latest_price['changePercent'] != 0:
                        difference_pct = latest_price['changePercent']
                    else:
                        # Calculate from open/close if available and not zero
                        if open_price > 0:
                            difference_pct = round((current_price - open_price) / open_price * 100, 2)
                        else:
                            difference_pct = 0
                    
                    latest_price = {
                        'symbol': stock,
                        'open': open_price,
                        'close': current_price,
                        'date': latest_price.get('date', 'unknown'),
                        'changePercent': difference_pct
                    }
                
                # Check if we've already processed this price point
                price_key = f"{stock}_{latest_price['date']}_{latest_price['close']:.2f}"
                if price_key not in prices_log:
                    prices_log.append(price_key)
                    
                    if 'changePercent' in latest_price and latest_price['changePercent'] != 0:
                        difference_pct = latest_price['changePercent']
                    else:
                        difference_pct = round((latest_price['close'] - latest_price['open']) / latest_price['open'] * 100, 2) if latest_price['open'] > 0 else 0
                    
                    print(f"Stock {stock} has a new price of {latest_price['close']} on {latest_price['date']} with a difference of {difference_pct}%")
                    
                    # Get company name for display
                    company_name = quote.get('companyName', stock)
                    stock_display = f"{stock} ({company_name})" if company_name and company_name != stock else stock
                    
                    if difference_pct > threshold_pct:
                        message = f"🔥Stock *{stock_display}* increased {difference_pct}% the last hour with a new price of {latest_price['close']} on {latest_price['date']}"
                        send_telegram_message(message)
                    elif difference_pct < -threshold_pct:
                        message = f"❌Stock *{stock_display}* decreased {difference_pct}% the last hour with a new price of {latest_price['close']} on {latest_price['date']}"
                        send_telegram_message(message)
                
                # Save the log
                with open(file_log_name, "w", encoding="utf-8") as f:
                    json.dump(prices_log, f, ensure_ascii=False, indent=2)
            else:
                print(f"⚠️ No interval data available for {stock}")
                    
        except Exception as e:
            print(f"❌ Error checking interval for {stock}: {e}")
            import traceback
            traceback.print_exc()


# ============================================================================
# COMBINED ALERT FUNCTIONS
# ============================================================================

def check_and_notify_52_week_highs_and_buy_dips(threshold_pct=0.5, buy_dip_pct=10.0):
    """
    Combined function to check both 52-week highs and buy dip opportunities
    (Maintains backward compatibility)
    """
    check_and_notify_52_week_highs(threshold_pct)
    check_and_notify_buy_dip_opportunities(buy_dip_pct)


def run_all_alerts(high_threshold=0.5, dip_threshold=10.0, ma_short=50, ma_long=200, interval_threshold=0.5):
    """
    Run all alert systems in sequence with strategic delays
    """
    print("🚀 Running all alert systems...")
    
    try:
        print("1. Checking 52-week highs...")
        check_and_notify_52_week_highs(high_threshold)
        
        # Add delay between alert types to avoid API hammering
        import time
        print("⏳ Cooling down between alert types (5s)...")
        time.sleep(5)
        
        print("2. Checking buy dip opportunities...")
        check_and_notify_buy_dip_opportunities(dip_threshold)
        
        print("⏳ Cooling down between alert types (5s)...")
        time.sleep(5)
        
        print("3. Checking moving average crossovers...")
        check_and_notify_ma_crossovers(ma_short, ma_long)
        
        print("⏳ Cooling down between alert types (5s)...")
        time.sleep(5)
        
        print("4. Checking intraday intervals...")
        run_and_notify_stock_interval(interval_threshold)
        
        print("✅ All alerts completed!")
        
    except Exception as e:
        print(f"❌ Error in alert system: {e}")
        send_telegram_message(f"❌ Alert system error: {e}")