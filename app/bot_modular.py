"""
Main Telegram Stock Alert Bot - Clean Modular Version

This is the production bot that orchestrates all the modular components.
For testing individual components, use test_bot.py instead.
"""
import sys
import os
import schedule
import time
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all our modular components
from core.telegram_client import send_telegram_message
from services.ai_research import research_company_with_telegram
from services.data_providers import test_data_providers_connectivity
from services.earnings import run_all_earnings, test_earnings_connectivity
from services.dividends import run_and_notify_dividend_calendar, test_dividend_connectivity
from analytics.alerts import (
    run_all_alerts, 
    check_and_notify_ma_crossovers, 
    check_and_notify_52_week_highs, 
    check_and_notify_buy_dip_opportunities
)
from config import (
    STOCKS_TO_CHECK, 
    ALERT_STOCK_INTERVAL, 
    ALERT_FX_INTERVAL, 
    ALERT_EARNINGS_INTERVAL,
    ALERT_DIVIDEND_INTERVAL,
    ALERT_MA_CROSSOVER_INTERVAL,
    ALERT_52_WEEK_HIGH_INTERVAL,
    ALERT_BUY_DIP_INTERVAL,
    BUY_DIP_THRESHOLD_PCT,
    MA_CROSSOVER_DAYS_LOOKBACK,
    STARTUP_DELAY_MA_CROSSOVER,
    STARTUP_DELAY_STOCK,
    STARTUP_DELAY_52_WEEK_HIGH,
    STARTUP_DELAY_BUY_DIP,
    STARTUP_DELAY_EARNINGS,
    STARTUP_DELAY_DIVIDENDS
)


class TelegramStockBot:
    """Main bot class that orchestrates all functionality"""
    
    # Global rate limiter to prevent simultaneous API calls across alert types
    _last_alert_run = 0
    _MIN_ALERT_SPACING = 30  # Minimum 30 seconds between different alert types
    
    def __init__(self):
        self.name = "Telegram Stock Alert Bot"
        self.version = "2.0.0 - Modular"
    
    def _rate_limit_alert(self, alert_name):
        """Ensure minimum spacing between different alert runs"""
        elapsed = time.time() - TelegramStockBot._last_alert_run
        if elapsed < TelegramStockBot._MIN_ALERT_SPACING:
            wait_time = TelegramStockBot._MIN_ALERT_SPACING - elapsed
            print(f"⏸️  Rate limiting: waiting {wait_time:.1f}s before running {alert_name}")
            time.sleep(wait_time)
        TelegramStockBot._last_alert_run = time.time()
        
    def startup_message(self):
        """Send bot startup message"""
        message = f"🤖 {self.name} v{self.version}\n"
        message += f"📊 Monitoring {len(STOCKS_TO_CHECK)} stocks: {', '.join(STOCKS_TO_CHECK)}\n"
        message += f"⏰ Alerts staggered over 90s (paid FMP)\n"
        message += f"💡 Quick check in 30s, alerts start in 20-90s"
        
        send_telegram_message(message)
        print(f"✅ {self.name} v{self.version} started!")
    
    def quick_startup_check(self):
        """Quick lightweight check at startup - just verify connectivity without full alerts"""
        print("\n🚀 Running quick startup connectivity check...")
        try:
            # Just get one quote to verify API is working
            from services.data_providers import get_stock_quote
            if STOCKS_TO_CHECK:
                test_symbol = STOCKS_TO_CHECK[0]
                quote = get_stock_quote(test_symbol)
                if quote:
                    price = quote.get('price', 'N/A')
                    msg = f"✅ Bot online! {test_symbol}: ${price}"
                    send_telegram_message(msg)
                    print(msg)
                else:
                    send_telegram_message("⚠️ Bot started but API check failed - will retry on schedule")
        except Exception as e:
            print(f"⚠️ Startup check error: {e}")
            send_telegram_message(f"⚠️ Bot started but connectivity check failed: {e}")
    
    def run_ma_crossover_alerts(self):
        """Run MA crossover alerts (Golden/Death Cross)"""
        self._rate_limit_alert("MA Crossover")
        print(f"\n📈 Running MA crossover alerts at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            check_and_notify_ma_crossovers(short_period=50, long_period=200, max_days_old=MA_CROSSOVER_DAYS_LOOKBACK)
        except Exception as e:
            error_msg = f"❌ MA crossover alerts error: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
    
    def run_52_week_high_alerts(self):
        """Run 52-week high alerts"""
        self._rate_limit_alert("52-Week High")
        print(f"\n🎯 Running 52-week high alerts at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            check_and_notify_52_week_highs(threshold_pct=0.5)
        except Exception as e:
            error_msg = f"❌ 52-week high alerts error: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
    
    def run_buy_dip_alerts(self):
        """Run buy dip opportunity alerts"""
        self._rate_limit_alert("Buy Dip")
        print(f"\n💰 Running buy dip alerts at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            check_and_notify_buy_dip_opportunities(dip_threshold_pct=BUY_DIP_THRESHOLD_PCT)
        except Exception as e:
            error_msg = f"❌ Buy dip alerts error: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
    
    def run_general_stock_alerts(self):
        """Run general stock spike alerts"""
        self._rate_limit_alert("General Stock")
        try:
            from analytics.alerts import run_and_notify_stock_interval
            run_and_notify_stock_interval(threshold_pct=0.5)
        except Exception as e:
            error_msg = f"❌ General stock alerts error: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
    
    def run_earnings_alerts(self):
        """Run earnings monitoring (scheduled based on ALERT_EARNINGS_INTERVAL)"""
        self._rate_limit_alert("Earnings")
        print(f"\n📊 Running earnings alerts at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            run_all_earnings()
        except Exception as e:
            error_msg = f"❌ Earnings error: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
    
    def run_dividend_alerts(self):
        """Run dividend calendar monitoring (scheduled based on ALERT_DIVIDEND_INTERVAL)"""
        self._rate_limit_alert("Dividends")
        print(f"\n💰 Running dividend alerts at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            run_and_notify_dividend_calendar()
        except Exception as e:
            error_msg = f"❌ Dividend alerts error: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
    
    def test_connectivity(self):
        """Test all API connections"""
        print("🧪 Testing API connectivity...")
        
        # Test data providers
        data_results = test_data_providers_connectivity()
        
        # Test earnings and dividends
        earnings_results = test_earnings_connectivity()
        dividend_results = test_dividend_connectivity()
        
        # Summary message
        message = "🧪 *API Connectivity Test Results*\n"
        message += f"📊 FMP Quote API: {'✅' if data_results['fmp'] else '❌'}\n"
        message += f"📈 Yahoo Finance API: {'✅' if data_results['yahoo_finance'] else '❌'}\n"
        message += f"📊 FMP Earnings API: {'✅' if earnings_results['earnings'] else '❌'}\n"
        message += f"💰 FMP Dividend API: {'✅' if dividend_results['dividends'] else '❌'}\n"
        message += f"📰 News API: ❌ Disabled (subscription required)"
        
        all_working = all([
            data_results['fmp'],
            data_results['yahoo_finance'], 
            earnings_results['earnings'],
            dividend_results['dividends']
        ])
        
        message += f"\n{'🎉 All systems operational!' if all_working else '⚠️ Some systems may have issues'}"
        
        send_telegram_message(message)
        return all_working
    
    def schedule_alerts(self):
        """Set up scheduled alerts with individual intervals"""
        print("⏰ Setting up scheduled alerts...")
        print("⏰ ALERT_MA_CROSSOVER_INTERVAL :", ALERT_MA_CROSSOVER_INTERVAL)
        print("⏰ ALERT_52_WEEK_HIGH_INTERVAL :", ALERT_52_WEEK_HIGH_INTERVAL)
        print("⏰ ALERT_BUY_DIP_INTERVAL :", ALERT_BUY_DIP_INTERVAL)
        print("⏰ ALERT_STOCK_INTERVAL :", ALERT_STOCK_INTERVAL)


        # Schedule each alert type with its own interval and staggered start times
        # This prevents all alerts from running simultaneously at startup
        
        # Create wrapper functions with staggered startup
        # Delays are configurable via .env (STARTUP_DELAY_* variables)
        # MA crossover runs early but chart generation happens before sending
        def delayed_ma_crossover():
            time.sleep(STARTUP_DELAY_MA_CROSSOVER)
            self.run_ma_crossover_alerts()  # Run once at startup
            while True:
                time.sleep(ALERT_MA_CROSSOVER_INTERVAL)
                self.run_ma_crossover_alerts()
                
        def delayed_52_week_high():
            time.sleep(STARTUP_DELAY_52_WEEK_HIGH)
            self.run_52_week_high_alerts()  # Run once at startup
            while True:
                time.sleep(ALERT_52_WEEK_HIGH_INTERVAL)
                self.run_52_week_high_alerts()
                
        def delayed_buy_dip():
            time.sleep(STARTUP_DELAY_BUY_DIP)
            self.run_buy_dip_alerts()  # Run once at startup
            while True:
                time.sleep(ALERT_BUY_DIP_INTERVAL)
                self.run_buy_dip_alerts()
                
        def delayed_stock_alerts():
            time.sleep(STARTUP_DELAY_STOCK)
            self.run_general_stock_alerts()  # Run once at startup
            while True:
                time.sleep(ALERT_STOCK_INTERVAL)
                self.run_general_stock_alerts()
                
        def delayed_earnings():
            time.sleep(STARTUP_DELAY_EARNINGS)
            self.run_earnings_alerts()  # Run once at startup
            while True:
                time.sleep(ALERT_EARNINGS_INTERVAL)
                self.run_earnings_alerts()
        
        def delayed_dividends():
            time.sleep(STARTUP_DELAY_DIVIDENDS)
            self.run_dividend_alerts()  # Run once at startup
            while True:
                time.sleep(ALERT_DIVIDEND_INTERVAL)
                self.run_dividend_alerts()
        
        # Use threading for parallel execution with staggered starts
        import threading
        self.ma_thread = threading.Thread(target=delayed_ma_crossover, daemon=True)
        self.high_thread = threading.Thread(target=delayed_52_week_high, daemon=True)
        self.dip_thread = threading.Thread(target=delayed_buy_dip, daemon=True)
        self.stock_thread = threading.Thread(target=delayed_stock_alerts, daemon=True)
        self.earnings_thread = threading.Thread(target=delayed_earnings, daemon=True)
        self.dividend_thread = threading.Thread(target=delayed_dividends, daemon=True)
        
        # Start all threads
        self.ma_thread.start()
        self.high_thread.start()
        self.dip_thread.start() 
        self.stock_thread.start()
        self.earnings_thread.start()
        self.dividend_thread.start()
        
        print(f"📅 Staggered startup delays configured (spread over 100s with paid FMP plan):")
        print(f"   ⏰ General Stock: starts in 20s, then every {ALERT_STOCK_INTERVAL/60:.1f} min")
        print(f"   🎯 52-Week Highs: starts in 40s, then every {ALERT_52_WEEK_HIGH_INTERVAL/60:.1f} min")
        print(f"   💰 Buy Dips: starts in 60s, then every {ALERT_BUY_DIP_INTERVAL/60:.1f} min")
        print(f"   📈 MA Crossovers: starts in 80s, then every {ALERT_MA_CROSSOVER_INTERVAL/60:.1f} min")
        print(f"   📊 Earnings: starts in 90s, then every {ALERT_EARNINGS_INTERVAL/60:.1f} min")
        print(f"   💰 Dividends: starts in 100s, then every {ALERT_DIVIDEND_INTERVAL/60:.1f} min")
        
        # Convert seconds to human readable format for display
        def format_interval(seconds):
            hours = seconds / 3600
            minutes = (seconds % 3600) / 60
            
            if hours >= 1:
                return f"{hours:.1f} hours" if hours != 1 else "1 hour"
            elif minutes >= 1:
                return f"{int(minutes)} minutes" if minutes != 1 else "1 minute"
            else:
                return f"{seconds} seconds"
        
        print("✅ Scheduled alerts configured:")
        print(f"   📈 MA Crossovers: every {format_interval(ALERT_MA_CROSSOVER_INTERVAL)} ({ALERT_MA_CROSSOVER_INTERVAL}s)")
        print(f"   🎯 52-Week Highs: every {format_interval(ALERT_52_WEEK_HIGH_INTERVAL)} ({ALERT_52_WEEK_HIGH_INTERVAL}s)")
        print(f"   💰 Buy Dips: every {format_interval(ALERT_BUY_DIP_INTERVAL)} ({ALERT_BUY_DIP_INTERVAL}s)")
        print(f"   ⏰ General Stock: every {format_interval(ALERT_STOCK_INTERVAL)} ({ALERT_STOCK_INTERVAL}s)")
        print(f"   📊 Earnings: every {format_interval(ALERT_EARNINGS_INTERVAL)} ({ALERT_EARNINGS_INTERVAL}s)")
        print(f"   💰 Dividends: every {format_interval(ALERT_DIVIDEND_INTERVAL)} ({ALERT_DIVIDEND_INTERVAL}s)")
    
    def run_scheduled_tasks(self):
        """Check if all alert threads are running (no-op since threads handle scheduling)"""
        # Since we're using threads with built-in delays, no need to run_pending
        # Just check if threads are alive
        threads_status = {
            'ma_crossover': getattr(self, 'ma_thread', None) and self.ma_thread.is_alive(),
            '52_week_high': getattr(self, 'high_thread', None) and self.high_thread.is_alive(),
            'buy_dip': getattr(self, 'dip_thread', None) and self.dip_thread.is_alive(),
            'stock_alerts': getattr(self, 'stock_thread', None) and self.stock_thread.is_alive(),
            'earnings': getattr(self, 'earnings_thread', None) and self.earnings_thread.is_alive(),
            'dividends': getattr(self, 'dividend_thread', None) and self.dividend_thread.is_alive()
        }
        
        # Only print status occasionally (every 60 calls = ~1 minute)
        if not hasattr(self, '_status_counter'):
            self._status_counter = 0
        self._status_counter += 1
        
        if self._status_counter % 60 == 0:  # Print every minute
            active_threads = sum(threads_status.values())
            print(f"🔄 Alert threads status: {active_threads}/6 active")
    
    def run_continuous(self):
        """Run bot in continuous mode with scheduled alerts"""
        print(f"\n🔄 Starting continuous monitoring...")
        print("Press Ctrl+C to stop")
        
        # Use a reasonable check interval - minimum 1 second, max 60 seconds
        check_interval = min(60, max(1, ALERT_STOCK_INTERVAL // 10))
        print(f"⏰ Checking for pending tasks every {check_interval} seconds")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(check_interval)
        except KeyboardInterrupt:
            print("\n⏹️ Bot stopped by user")
            send_telegram_message("⏹️ Telegram Stock Bot stopped")
    
    def manual_alerts_once(self):
        """Run all alerts once (manual trigger)"""
        print("\n🔧 Running manual alerts (one-time)...")
        print("Running all alert types...")
        self.run_ma_crossover_alerts()
        self.run_52_week_high_alerts() 
        self.run_buy_dip_alerts()
        self.run_general_stock_alerts()
        self.run_earnings_alerts()
        print("✅ Manual alerts completed")


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description="Telegram Stock Alert Bot v2.0")
    parser.add_argument('--test', action='store_true', help='Test API connectivity only')
    parser.add_argument('--once', action='store_true', help='Run alerts once and exit')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring (default)')
    
    args = parser.parse_args()
    
    # Initialize bot
    bot = TelegramStockBot()
    
    try:
        # Send startup message
        bot.startup_message()
        
        if args.test:
            # Test mode - just check connectivity
            print("🧪 Testing mode - checking API connectivity")
            success = bot.test_connectivity()
            sys.exit(0 if success else 1)
            
        elif args.once:
            # Run once mode
            print("🔧 One-time mode - running all alerts once")
            bot.manual_alerts_once()
            sys.exit(0)
            
        else:
            # Default: continuous monitoring
            print("🔄 Continuous monitoring mode")
            
            # Run quick startup check (single API call)
            bot.quick_startup_check()
            
            # Then schedule full alerts with staggered delays
            bot.schedule_alerts()
            bot.run_continuous()
            
    except Exception as e:
        error_msg = f"❌ Fatal error in main bot: {e}"
        print(error_msg)
        try:
            send_telegram_message(error_msg)
        except:
            pass  # Don't crash if telegram is unavailable
        sys.exit(1)


if __name__ == "__main__":
    main()