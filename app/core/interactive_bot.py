"""
Interactive Telegram Bot Handler
Handles incoming user messages and commands for stock configuration and alerts
"""
import os
import sys
import time
import traceback
from typing import Dict, Optional, Callable

# Add app directory to path  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telegram_client import send_telegram_message, get_telegram_updates, TELEGRAM_CHAT_ID, clear_chat_history
from services.ai_research import research_company_with_telegram, brief_company_summary_with_telegram  
from services.data_providers import (
    get_stock_quote, 
    get_cached_company_name, 
    add_company_name_to_cache,
    remove_company_name_from_cache
)
from services.market_sentiment import calculate_market_sentiment, format_sentiment_message
from utils.persistence import load_stock_list, save_stock_list


class InteractiveTelegramBot:
    """Interactive Telegram Bot for handling user commands and stock queries"""
    
    def __init__(self):
        self.last_update_id = 0
        self.running = False
        
        # Command mapping
        self.commands: Dict[str, Callable] = {
            '/start': self.cmd_start,
            '/help': self.cmd_help,
            '/stocks': self.cmd_list_stocks,
            '/add': self.cmd_add_stock,
            '/remove': self.cmd_remove_stock,
            '/research': self.cmd_research_stock,
            '/quote': self.cmd_quote_stock,
            '/market': self.cmd_market_sentiment,
            '/status': self.cmd_status,
            '/clear': self.cmd_clear_chat,
        }
        
        print(f"🤖 Interactive Telegram bot initialized with {len(self.commands)} commands")
    
    def process_message(self, message):
        """Process incoming Telegram message"""
        chat_id = message.get('chat', {}).get('id')
        user_name = message.get('from', {}).get('first_name', 'User')
        text = message.get('text', '').strip()
        
        # Security check - only respond to authorized chat
        if chat_id != int(TELEGRAM_CHAT_ID):
            print(f"❌ Unauthorized access attempt from {chat_id}")
            return
        
        if not text:
            return
            
        print(f"📨 Received message from {user_name} ({chat_id}): {text}")
        
        # Check if it's a command
        if text.startswith('/'):
            parts = text.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if command in self.commands:
                try:
                    self.commands[command](args, user_name)
                except Exception as e:
                    print(f"❌ Command error: {e}")
                    send_telegram_message(f"❌ Error executing {command}: {e}")
            else:
                send_telegram_message(f"❓ Unknown command: {command}\nUse /help to see available commands")
        else:
            # Handle non-command text as research query (USER-INITIATED ONLY)
            self.handle_research_query(text, user_name)
    
    def handle_research_query(self, text, user_name):
        """Handle non-command text as brief company summary (USER-INITIATED ONLY)"""
        # Check if it looks like a stock symbol (1-5 uppercase letters)
        text_upper = text.upper().strip()
        if len(text_upper) <= 5 and text_upper.isalpha():
            send_telegram_message(f"� Getting brief summary for {text_upper}...")
            try:
                brief_company_summary_with_telegram(text_upper)
            except Exception as e:
                send_telegram_message(f"❌ Brief summary failed for {text_upper}: {e}")
        else:
            send_telegram_message(f"💡 Tip: Send a stock symbol (e.g., AAPL) for brief summary, or use /help for commands")
    
    # ============================================================================
    # COMMAND HANDLERS
    # ============================================================================
    
    def cmd_start(self, args, user_name):
        """Handle /start command"""
        message = f"🚀 Welcome {user_name}!\n\n"
        message += "I'm your Stock Alert Bot. I provide:\n"
        message += "📊 Stock price alerts & monitoring\n"
        message += "💰 Real-time quotes and metrics\n"
        message += "🎯 Golden Cross & technical alerts\n"
        message += "📈 Earnings & dividend notifications\n"
        message += "⚙️ Customizable watchlist management\n\n"
        message += "Use /help to see all commands!"
        
        send_telegram_message(message)
    
    def cmd_help(self, args, user_name):
        """Handle /help command"""
        message = "🤖 **Stock Alert Bot Commands**\n\n"
        
        message += "📊 **Stock Management:**\n"
        message += "• `/stocks` - View current watchlist\n"
        message += "• `/add SYMBOL` - Add stock to watchlist\n"
        message += "• `/remove SYMBOL` - Remove stock from watchlist\n\n"
        
        message += "📈 **Price & Data:**\n"
        message += "• `/quote SYMBOL` - Get current stock price & metrics\n"
        message += "• `/market` - Get market sentiment (Fear & Greed Index)\n\n"
        
        message += "🔍 **Research & Analysis:**\n"
        message += "• `/research SYMBOL` - Get comprehensive AI analysis\n"
        message += "• `SYMBOL` - Brief company summary (just send stock symbol)\n\n"
        
        message += "🤖 **Bot Info:**\n"
        message += "• `/status` - Bot status and info\n"
        message += "• `/help` - Show this help message\n"
        message += "• `/clear` - Clear chat history\n\n"
        
        message += "🚨 **Alert Types:**\n"
        message += "• Price spikes & drops\n"
        message += "• 52-week highs & lows\n"
        message += "• Golden Cross (MA crossovers)\n"
        message += "• Earnings releases\n"
        message += "• Dividend announcements\n\n"
        
        message += "💡 **Examples:**\n"
        message += "`/add TSLA` - Add Tesla to watchlist\n"
        message += "`/quote AAPL` - Get Apple price & metrics\n"
        message += "`/market` - Check market sentiment\n"
        message += "`MSFT` - Brief Microsoft summary\n"
        message += "`/research NVDA` - Full NVIDIA analysis\n"
        message += "`/stocks` - View your watchlist"
        
        send_telegram_message(message)
    
    def cmd_list_stocks(self, args, user_name):
        """Handle /stocks command"""
        current_stocks = load_stock_list()
        
        if not current_stocks:
            send_telegram_message("📭 Your watchlist is empty.\nUse `/add SYMBOL` to add stocks.")
            return
        
        message = f"📊 **Your Watchlist ({len(current_stocks)} stocks):**\n\n"
        for i, stock in enumerate(current_stocks, 1):
            # Get company name from cache
            company_name = get_cached_company_name(stock)
            if company_name:
                message += f"{i}. **{stock}** - {company_name}\n"
            else:
                message += f"{i}. **{stock}**\n"
        
        message += f"\n💡 Use `/add SYMBOL` to add more or `/remove SYMBOL` to remove stocks."
        
        send_telegram_message(message)
    
    def cmd_add_stock(self, args, user_name):
        """Handle /add command"""
        if not args:
            send_telegram_message("❓ Please specify a stock symbol.\n\nExample: `/add TSLA`")
            return
        
        symbol = args[0].upper()
        current_stocks = load_stock_list()
        
        # Check if already in watchlist
        if symbol in current_stocks:
            send_telegram_message(f"ℹ️ {symbol} is already in your watchlist.\nUse `/stocks` to see all stocks.")
            return
        
        # Validate stock by getting quote
        quote_data = get_stock_quote(symbol)
        
        if not quote_data:
            send_telegram_message(f"❌ Cannot find stock data for {symbol}. Please check the symbol.")
            return
        
        # Add to watchlist
        current_stocks.append(symbol)
        success = save_stock_list(current_stocks)
        
        if success:
            company_name = quote_data.get('companyName', symbol)
            
            # Cache the company name for future use
            if company_name and company_name != symbol:
                add_company_name_to_cache(symbol, company_name)
            
            price = quote_data.get('price', 'N/A')
            message = f"✅ **Added {symbol} to watchlist!**\n"
            message += f"🏢 {company_name}\n"
            message += f"💰 Current Price: ${price}\n"
            message += f"📊 Total stocks monitored: {len(current_stocks)}"
            send_telegram_message(message)
        else:
            send_telegram_message(f"❌ Failed to save {symbol} to watchlist")
    
    def cmd_remove_stock(self, args, user_name):
        """Handle /remove command"""
        if not args:
            send_telegram_message("❓ Please specify a stock symbol to remove.\n\nExample: `/remove TSLA`")
            return
        
        symbol = args[0].upper()
        current_stocks = load_stock_list()
        
        if symbol not in current_stocks:
            send_telegram_message(f"ℹ️ {symbol} is not in your watchlist.\nUse `/stocks` to see current stocks.")
            return
        
        current_stocks.remove(symbol)
        success = save_stock_list(current_stocks)
        
        if success:
            # Remove from company name cache
            remove_company_name_from_cache(symbol)
            
            message = f"✅ **Removed {symbol} from watchlist**\n"
            message += f"📊 Remaining stocks: {len(current_stocks)}"
            if current_stocks:
                message += f"\n📋 Current watchlist: {', '.join(current_stocks)}"
            send_telegram_message(message)
        else:
            send_telegram_message(f"❌ Failed to remove {symbol} from watchlist")
    
    def cmd_research_stock(self, args, user_name):
        """Handle /research command"""
        if not args:
            send_telegram_message("❓ Please specify a stock symbol for research.\n\nExample: `/research AAPL`")
            return
        
        symbol = args[0].upper()
        send_telegram_message(f"🔍 Researching {symbol} for {user_name}...")
        
        try:
            research_company_with_telegram(symbol)
        except Exception as e:
            send_telegram_message(f"❌ Research failed for {symbol}: {e}")
    
    def cmd_quote_stock(self, args, user_name):
        """Handle /quote command"""
        if not args:
            send_telegram_message("❓ Please specify a stock symbol for quote.\n\nExample: `/quote AAPL`")
            return
        
        symbol = args[0].upper()
        
        try:
            quote_data = get_stock_quote(symbol)
            
            if not quote_data:
                send_telegram_message(f"❌ Cannot find stock data for {symbol}. Please check the symbol.")
                return
            
            # Format the quote message
            company_name = quote_data.get('companyName', quote_data.get('name', symbol))
            price = quote_data.get('price', 'N/A')
            change = quote_data.get('change', 'N/A')
            change_percent = quote_data.get('changesPercentage', 'N/A')
            volume = quote_data.get('volume', 'N/A')
            market_cap = quote_data.get('marketCap', 'N/A')
            
            # Format volume and market cap
            if isinstance(volume, (int, float)) and volume > 0:
                if volume >= 1_000_000:
                    volume_formatted = f"{volume/1_000_000:.1f}M"
                elif volume >= 1_000:
                    volume_formatted = f"{volume/1_000:.1f}K"
                else:
                    volume_formatted = f"{volume:,.0f}"
            else:
                volume_formatted = "N/A"
            
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                if market_cap >= 1_000_000_000_000:  # Trillions
                    cap_formatted = f"${market_cap/1_000_000_000_000:.2f}T"
                elif market_cap >= 1_000_000_000:  # Billions
                    cap_formatted = f"${market_cap/1_000_000_000:.1f}B"
                elif market_cap >= 1_000_000:  # Millions
                    cap_formatted = f"${market_cap/1_000_000:.1f}M"
                else:
                    cap_formatted = f"${market_cap:,.0f}"
            else:
                cap_formatted = "N/A"
            
            # Create message
            message = f"📈 **{symbol} - {company_name}**\n\n"
            message += f"💰 **Price:** ${price}\n"
            
            if isinstance(change, (int, float)) and isinstance(change_percent, (int, float)):
                change_emoji = "📈" if change >= 0 else "📉"
                sign = "+" if change >= 0 else ""
                message += f"{change_emoji} **Change:** {sign}${change:.2f} ({sign}{change_percent:.2f}%)\n"
            
            message += f"📊 **Volume:** {volume_formatted}\n"
            message += f"🏢 **Market Cap:** {cap_formatted}\n"
            
            send_telegram_message(message)
            
        except Exception as e:
            print(f"❌ Quote error: {e}")
            send_telegram_message(f"❌ Failed to get quote for {symbol}: {e}")
    
    def cmd_market_sentiment(self, args, user_name):
        """Handle /market command - show market sentiment index"""
        send_telegram_message("🔍 Calculating market sentiment...")
        
        try:
            sentiment = calculate_market_sentiment()
            message = format_sentiment_message(sentiment)
            send_telegram_message(message)
        except Exception as e:
            print(f"❌ Market sentiment error: {e}")
            traceback.print_exc()
            send_telegram_message(f"❌ Failed to calculate market sentiment: {e}")
    
    def cmd_status(self, args, user_name):
        """Handle /status command"""
        current_stocks = load_stock_list()
        
        message = f"🤖 **Bot Status**\n\n"
        message += f"👤 **User:** {user_name}\n"
        message += f"📊 **Watchlist:** {len(current_stocks)} stocks\n"
        message += f"🟢 **Status:** Online & Active\n"
        message += f"🔄 **Features:** Alerts + Interactive Commands\n\n"
        
        if current_stocks:
            message += f"📋 **Monitoring:** {', '.join(current_stocks[:10])}"
            if len(current_stocks) > 10:
                message += f" +{len(current_stocks)-10} more"
        else:
            message += "💡 **Tip:** Add stocks with `/add SYMBOL`"
        
        send_telegram_message(message)
    
    def cmd_clear_chat(self, args, user_name):
        """Handle /clear command - clear chat history"""
        send_telegram_message(f"🧹 Clearing chat history for {user_name}...")
        
        try:
            clear_chat_history(max_messages=50)  # Clear last 50 messages
            send_telegram_message("✅ **Chat history cleared!**\n\nSend /help to see all commands!")
        except Exception as e:
            send_telegram_message(f"❌ Failed to clear chat history: {e}")
    
    # ============================================================================
    # BOT RUNNER
    # ============================================================================
    
    def run(self):
        """Main bot loop"""
        self.running = True
        send_telegram_message("🤖 Interactive bot started! Send /help for commands.")
        
        print("🤖 Interactive Telegram bot listening for messages...")
        print("💡 Users can now send commands and stock symbols for research")
        
        while self.running:
            try:
                updates = get_telegram_updates(self.last_update_id + 1)
                
                if updates and 'result' in updates:
                    for update in updates['result']:
                        if 'update_id' in update:
                            self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            self.process_message(update['message'])
                
                # Short delay to prevent excessive API calls
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🛑 Interactive bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Bot error: {e}")
                time.sleep(5)  # Wait longer on errors
        
        self.running = False
        send_telegram_message("🛑 Interactive bot stopped")
    
    def stop(self):
        """Stop the bot"""
        self.running = False


def run_interactive_bot():
    """Main function to run the interactive bot"""
    print("🚀 Starting Interactive Telegram Stock Bot...")
    
    try:
        bot = InteractiveTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    run_interactive_bot()