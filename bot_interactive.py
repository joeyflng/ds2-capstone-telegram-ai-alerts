#!/usr/bin/env python3
"""
Combined Telegram Stock Bot - Interactive + Alerts
Runs both scheduled alerts and interactive command handling
"""
import sys
import os
import time
import signal
import threading
from threading import Thread

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

# Import bot modules
from bot_modular import TelegramStockBot
from core.interactive_bot import InteractiveTelegramBot
from core.telegram_client import send_telegram_message, clear_chat_history


class CombinedTelegramBot:
    """Runs both alert bot and interactive bot in parallel"""
    
    def __init__(self):
        self.alert_bot = TelegramStockBot()
        self.interactive_bot = InteractiveTelegramBot()
        self.running = False
        
        # Threads for parallel execution
        self.alert_thread = None
        self.interactive_thread = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {sig}, shutting down...")
        self.stop()
    
    def run_alert_bot(self):
        """Run the scheduled alert bot"""
        try:
            print("🚀 Starting scheduled alerts system...")
            self.alert_bot.startup_message()
            self.alert_bot.schedule_alerts()
            
            # Alert threads now handle their own scheduling with staggered delays
            # Just keep the main alert thread alive and occasionally check status
            while self.running:
                self.alert_bot.run_scheduled_tasks()  # Just checks thread status now
                time.sleep(10)  # Check every 10 seconds instead of every 1 second
                
        except Exception as e:
            print(f"❌ Alert bot error: {e}")
            send_telegram_message(f"❌ Alert system error: {e}")
    
    def run_interactive_bot(self):
        """Run the interactive command bot"""
        try:
            print("🤖 Starting interactive command system...")
            # Small delay to let alert bot start first
            time.sleep(2)
            self.interactive_bot.run()
        except Exception as e:
            print(f"❌ Interactive bot error: {e}")
            send_telegram_message(f"❌ Interactive system error: {e}")
    
    def start(self):
        """Start both bots in parallel"""
        self.running = True
        
        # Clear chat history on startup
        # print("🧹 Clearing previous chat messages...")
        # clear_chat_history(max_messages=30)  # Clear last 30 messages
        
        # Send startup message
        message = "🚀 Stock Alert Bot Ready to help with your stock research! 📈"
        # message = "🚀 **Stock Alert Bot Restarted! **\n\n"
        # message += "🧹 **Chat History Cleared** - Fresh start\n"
        # message += "✅ **Scheduled Alerts**: Running every hour\n"
        # message += "🤖 **Interactive Commands**: Ready for your requests\n\n"
        # message += "💡 **Quick Start:**\n"
        # message += "• Send `AAPL` for brief company summary\n"
        # message += "• Send `/quote MSFT` for price & metrics\n"
        # message += "• Send `/research NVDA` for full AI analysis\n"
        # message += "• Send `/help` to see all commands\n\n"
        
        send_telegram_message(message)
        
        # Start alert bot in separate thread
        self.alert_thread = Thread(target=self.run_alert_bot, daemon=True)
        self.alert_thread.start()
        
        # Start interactive bot in separate thread  
        self.interactive_thread = Thread(target=self.run_interactive_bot, daemon=True)
        self.interactive_thread.start()
        
        print("🎉 Both bots started successfully!")
        print("📊 Alerts: Running scheduled alerts every hour")
        print("🤖 Interactive: Listening for Telegram commands")
        print("Press Ctrl+C to stop both bots")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop both bots gracefully"""
        self.running = False
        
        print("🛑 Stopping both bots...")
        
        # Stop interactive bot
        if self.interactive_bot:
            self.interactive_bot.stop()
        
        # Wait for threads to finish
        if self.alert_thread and self.alert_thread.is_alive():
            print("⏳ Waiting for alert bot to stop...")
            self.alert_thread.join(timeout=5)
        
        if self.interactive_thread and self.interactive_thread.is_alive():
            print("⏳ Waiting for interactive bot to stop...")
            self.interactive_thread.join(timeout=5)
        
        send_telegram_message("🛑 Stock Alert Bot stopped - both alerts and commands disabled")
        print("✅ Both bots stopped successfully")


def main():
    """Main entry point"""
    print("🚀 Starting Combined Telegram Stock Bot...")
    print("📊 Features: Scheduled Alerts + Interactive Commands")
    
    bot = CombinedTelegramBot()
    try:
        bot.start()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        bot.stop()


if __name__ == "__main__":
    main()