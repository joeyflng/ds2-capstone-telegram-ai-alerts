"""
AI Market Chat Companion - Streamlit Web App
Interactive market data analysis with AI-powered insights
"""
import os
import sys

# Force unbuffered output for HF logs
sys.stdout = sys.stderr
sys.stdout.reconfigure(line_buffering=True)

# Debug: Print startup info (visible in HF logs) - Disabled for production
# Uncomment these lines for debugging deployment issues
# print("=" * 60, flush=True)
# print("🚀 Starting AI Market Chat Companion", flush=True)
# print(f"Working directory: {os.getcwd()}", flush=True)
# print(f"Files in current dir: {os.listdir('.')[:10]}", flush=True)
# print(f"App folder exists: {os.path.exists('app')}", flush=True)
# if os.path.exists('app'):
#     print(f"App folder contents: {os.listdir('app')[:10]}", flush=True)
# print("=" * 60, flush=True)

# Patch os.getenv to support Streamlit secrets BEFORE any other imports
_original_getenv = os.getenv

def _patched_getenv(key, default=None):
    """Check Streamlit secrets first, then fall back to environment variables"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return _original_getenv(key, default)

os.getenv = _patched_getenv

# Add current directory to path for config import (Hugging Face compatibility)
# On HF Spaces, __file__ exists but we need both the script dir and cwd
if '__file__' in globals():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir and script_dir not in sys.path:
        sys.path.insert(0, script_dir)
# Also add current working directory
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)

# Now safe to import other modules
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
from typing import Dict, Optional

# Inline config (avoids circular import issues on HF)
class WebConfig:
    """Web app configuration"""
    def __init__(self):
        # Try Streamlit secrets first (HF Spaces), then environment variables
        self.GROQ_API_KEY = self._get_env("GROQ_API_KEY", "")
        self.FMP_API_KEY = self._get_env("FMP_API_KEY", "")
        self.FMP_DELAY_SECONDS = 3
    
    def _get_env(self, key: str, default: str = "") -> str:
        """Get environment variable with HF Spaces support"""
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except Exception:
            pass
        return os.getenv(key, default)

web_config = WebConfig()

# Debug: Show config status
print(f"🔑 API Keys loaded: FMP={'✅' if web_config.FMP_API_KEY else '❌'}, GROQ={'✅' if web_config.GROQ_API_KEY else '❌'}", flush=True)

# Import our utilities
from utils.market import (
    fetch_prices, fetch_current_quote, get_basic_stats, compute_rsi, compute_volatility,
    get_trend_signal, get_company_info, validate_ticker, POPULAR_TICKERS,
    format_price, format_market_cap, format_volume, get_fear_greed_index, format_fear_greed_score
)
from utils.llm import (
    generate_response, get_available_providers, get_preset_questions,
    format_llm_response, test_llm_connectivity
)

# Cache expensive API calls to prevent rerun overhead
@st.cache_data(ttl=60)
def cached_fetch_current_quote(ticker: str):
    """Cache current quote for 60 seconds to avoid API calls on reruns"""
    return fetch_current_quote(ticker)

@st.cache_data(ttl=300)
def cached_get_fear_greed_index():
    """Cache fear & greed index for 5 minutes"""
    return get_fear_greed_index()

@st.cache_data(ttl=300)
def cached_get_basic_stats(df, df_1y=None):
    """Cache basic stats for 5 minutes"""
    return get_basic_stats(df, df_1y)

@st.cache_data(ttl=300)
def cached_get_company_info(ticker: str):
    """Cache company info for 5 minutes"""
    return get_company_info(ticker)

# ...existing code...

# Page configuration
st.set_page_config(
    page_title="AI Market Chat Companion",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .bullish { color: #00ff88; font-weight: bold; }
    .bearish { color: #ff4444; font-weight: bold; }
    .neutral { color: #ffaa00; font-weight: bold; }
    .chat-message { 
        background: #f0f2f6; 
        padding: 1rem; 
        border-radius: 10px; 
        margin: 0.5rem 0; 
        border-left: 4px solid #667eea;
    }
    .ai-response {
        background: #e8f4f8;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #2e8b57;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.title("📊 AI Market Chat Companion")
    st.markdown("*Interactive market analysis with AI-powered insights*")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Debug info (collapsible)
        with st.expander("🔍 System Info", expanded=False):
            fmp_key_set = bool(web_config.FMP_API_KEY)
            groq_key_set = bool(web_config.GROQ_API_KEY)
            
            st.caption(f"**FMP API:** {'✅ Configured' if fmp_key_set else '❌ Missing'}")
            st.caption(f"**Groq API:** {'✅ Configured' if groq_key_set else '❌ Missing'}")
            
            # Check if running on HF
            if 'SPACE_ID' in os.environ:
                st.caption(f"**Platform:** 🤗 Hugging Face Space")
            else:
                st.caption(f"**Platform:** 💻 Local")
        
        # LLM Provider Selection
        providers = get_available_providers()
        available_providers = [k for k, v in providers.items() if v]
        
        if available_providers:
            # Prioritize Groq in the dropdown
            provider_order = ['groq', 'gemini', 'openai']
            ordered_providers = [p for p in provider_order if p in available_providers]
            ordered_providers.extend([p for p in available_providers if p not in ordered_providers])
            
            llm_provider = st.selectbox(
                "🤖 AI Provider",
                ordered_providers,
                help="Choose your AI provider. Groq is recommended (free & fast!)"
            )
        else:
            st.error("❌ No AI providers configured!")
            st.markdown("""
            **🚀 Quick Setup - Get Groq API Key (FREE):**
            1. Visit: https://console.groq.com/keys
            2. Sign up (no credit card needed)
            3. Create API key
            4. Add to .env file: `GROQ_API_KEY=your_key`
            5. Restart app
            """)
            llm_provider = None
        
        # Provider status
        st.subheader("📡 API Status")
        # Only display Groq status
        for provider, status in providers.items():
            if provider == 'groq':  # Only show Groq
                status_icon = "✅" if status else "❌"
                if not status:
                    st.markdown(f"{status_icon} **{provider.title()}** - [Get FREE key →](https://console.groq.com/keys)")
                else:
                    st.write(f"{status_icon} {provider.title()}")
        
        # Quick setup guide
        if not any(providers.values()):
            st.markdown("""
            ### 🚀 Quick Setup
            **Groq (Recommended - FREE):**
            1. Visit [console.groq.com](https://console.groq.com/keys)
            2. Sign up (no card required)
            3. Create API key
            4. Add to `.env`: 
               ```
               GROQ_API_KEY=your_key_here
               ```
            5. Restart app
            """)
        
        # Test connectivity button
        if st.button("🧪 Test AI Connectivity"):
            with st.spinner("Testing AI connections..."):
                results = test_llm_connectivity()
                for provider, result in results.items():
                    if "✅" in result:
                        st.success(f"**{provider.title()}**: {result}")
                    else:
                        st.error(f"**{provider.title()}**: {result}")
        
        st.divider()
        
        # Fear and Greed Index
        st.subheader("😰😊 Market Sentiment")
        try:
            with st.spinner("Loading Fear & Greed Index..."):
                fear_greed = cached_get_fear_greed_index()  # ✅ Using cached version
            
            # Create a color for the score
            score = fear_greed['score']
            if score >= 75:
                color = "#ff6b6b"  # Red for extreme greed
            elif score >= 55:
                color = "#ffa726"  # Orange for greed
            elif score >= 45:
                color = "#66bb6a"  # Green for neutral
            elif score >= 25:
                color = "#42a5f5"  # Blue for fear
            else:
                color = "#ab47bc"  # Purple for extreme fear
            
            st.markdown(f"""
            <div style="text-align: center; padding: 10px; border-radius: 10px; background: linear-gradient(45deg, {color}20, {color}10);">
                <h3 style="margin: 0; color: {color};">{fear_greed['emoji']} {fear_greed['rating']}</h3>
                <p style="margin: 0; font-size: 0.8em; opacity: 0.8;">{fear_greed['description']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"Source: {fear_greed['source'].upper()} | Updated: {datetime.fromisoformat(fear_greed['timestamp'].replace('Z', '+00:00')).strftime('%H:%M')}")
            
        except Exception as e:
            st.error(f"❌ Unable to load market sentiment: {e}")
        
        st.divider()
        
        # Telegram Bot Commands section in sidebar
        st.subheader("📱 Telegram Bot")
        
        # Get current ticker for command generation
        current_ticker = st.session_state.get('current_ticker', 'AAPL')
        
        # Create dropdown for different command options
        command_options = {
            f"Add {current_ticker} to watchlist": f"/add {current_ticker}",
            f"Get {current_ticker} quote": f"/quote {current_ticker}",
            f"Research {current_ticker}": f"/research {current_ticker}",
            f"Brief {current_ticker} summary": current_ticker,
            "View watchlist": "/stocks",
            "Bot help": "/help"
        }
        
        selected_action = st.selectbox(
            "Choose command:",
            list(command_options.keys()),
            key="telegram_command_sidebar"
        )
        
        telegram_command = command_options[selected_action]
        
        # Show the command
        st.code(telegram_command, language="text")
        
        st.caption("Copy and paste this command into your Telegram bot")
        
        # Show available bot commands
        with st.expander("🤖 All Bot Commands"):
            st.markdown("""
            **📊 Stock Management:**
            - `/stocks` - View watchlist
            - `/add SYMBOL` - Add to watchlist  
            - `/remove SYMBOL` - Remove
            
            **📈 Price & Data:**
            - `/quote SYMBOL` - Get price
            
            **🔍 Research:**
            - `/research SYMBOL` - AI analysis
            - `SYMBOL` - Brief summary
            
            **🤖 Bot Info:**
            - `/help` - Show commands
            """)
        
        st.divider()
        
        # Quick ticker suggestions
        st.subheader("🔥 Popular Tickers")
        for category, tickers in POPULAR_TICKERS.items():
            with st.expander(f"📈 {category}"):
                for ticker in tickers:
                    if st.button(ticker, key=f"quick_{ticker}"):
                        st.session_state['selected_ticker'] = ticker
                        st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.header("🎯 Ticker Analysis")
        
        # Ticker input
        default_ticker = st.session_state.get('selected_ticker', 'AAPL')
        ticker = st.text_input(
            "Enter Stock Symbol",
            value=default_ticker,
            placeholder="e.g., AAPL, TSLA, BTC-USD",
            help="Enter any valid stock symbol, crypto, or ETF"
        ).upper()
        
        if ticker:
            # Check if we already have data for this ticker cached
            # This prevents refetching when only changing telegram command selection
            use_cached = (
                'current_ticker' in st.session_state and 
                st.session_state['current_ticker'] == ticker and
                'current_df' in st.session_state and
                not st.session_state['current_df'].empty
            )
            
            # Validate ticker
            if validate_ticker(ticker):
                # Set the period for data fetching
                period = "30d"
                
                # Use cached data if available, otherwise fetch new
                if use_cached:
                    df = st.session_state['current_df']
                    df_1y = st.session_state.get('current_df_1y', None)
                else:
                    # Fetch new data
                    with st.spinner(f"📊 Fetching data for {ticker}..."):
                        df = fetch_prices(ticker, period)
                        
                        # Also fetch 1-year data for 52-week high/low calculation
                        df_1y = None
                        if period != '1y':
                            try:
                                df_1y = fetch_prices(ticker, '1y')
                            except Exception as e:
                                print(f"Warning: Could not fetch 1-year data for 52-week calculations: {e}")
                        
                        # Store in session state for reuse
                        st.session_state['current_df'] = df
                        st.session_state['current_df_1y'] = df_1y
                        st.session_state['current_ticker'] = ticker
                    
                if not df.empty:
                    # Check if this is mock data (approximate check)
                    is_mock_data = len(df) == 30 and df.index[-1].hour == 0
                    
                    if is_mock_data:
                        st.warning("⚠️ **Demo Mode**: Using simulated data due to network restrictions. Real-time data may not be available.")
                    
                    # Get real-time quote for current price (more accurate than historical data)
                    current_quote = cached_fetch_current_quote(ticker)  # ✅ Using cached version
                    
                    # Calculate metrics from historical data (pass 1y data for 52-week calcs)
                    stats = cached_get_basic_stats(df, df_1y)  # ✅ Using cached version

                    rsi = compute_rsi(df)
                    volatility = compute_volatility(df, period=30)  # 30-day volatility
                    
                    # Override with real-time quote data if available (includes accurate 52W high/low)
                    if current_quote and 'price' in current_quote:
                        real_time_price = current_quote['price']
                        historical_price = stats.get('current_price', real_time_price)
                        
                        # Calculate daily change using real-time price vs yesterday's close
                        if len(df) > 1:
                            previous_close = df['Close'].iloc[-2]
                            daily_change = real_time_price - previous_close
                            daily_change_pct = (daily_change / previous_close) * 100 if previous_close != 0 else 0
                        else:
                            daily_change = stats.get('daily_change', 0)
                            daily_change_pct = stats.get('daily_change_pct', 0)
                        
                        # Update stats with real-time data (including FMP's accurate 52W high/low)
                        stats.update({
                            'current_price': real_time_price,
                            'daily_change': daily_change,
                            'daily_change_pct': daily_change_pct
                        })
                        
                        # Use FMP's accurate 52-week high/low if available
                        if 'yearHigh' in current_quote or 'week52High' in current_quote:
                            stats['high_52w'] = current_quote.get('yearHigh') or current_quote.get('week52High', stats.get('high_52w'))
                        if 'yearLow' in current_quote or 'week52Low' in current_quote:
                            stats['low_52w'] = current_quote.get('yearLow') or current_quote.get('week52Low', stats.get('low_52w'))
                    
                    # Add calculated metrics to stats
                    stats.update({
                        'rsi': rsi,
                        'volatility': volatility
                    })
                    
                    # Get simplified trend signal based on RSI only
                    if rsi > 70:
                        trend_signal, trend_emoji = "overbought", "🟡"
                    elif rsi < 30:
                        trend_signal, trend_emoji = "oversold", "🟡"
                    elif 40 <= rsi <= 60:
                        trend_signal, trend_emoji = "neutral", "🟡"
                    else:
                        trend_signal, trend_emoji = "trending", "🟢"
                    stats.update({
                        'trend_signal': trend_signal,
                        'trend_emoji': trend_emoji
                    })
                    
                    # Get company info with error handling
                    # Get company info with error handling
                    try:
                        company_info = cached_get_company_info(ticker)  # ✅ Using cached version
                    except Exception as e:
                        st.error(f"Unable to fetch company info: {e}")
                        company_info = {
                            'name': ticker.upper(),
                            'sector': 'Unknown',
                            'industry': 'Unknown',
                            'market_cap': 0,
                            'description': 'Error loading company information'
                        }
                    
                    # Display current price and change
                    col_price, col_change = st.columns(2)
                    
                    with col_price:
                        st.metric(
                            "💰 Current Price",
                            format_price(stats['current_price'])
                        )
                    
                    with col_change:
                        change_color = "bullish" if stats['daily_change'] >= 0 else "bearish"
                        st.metric(
                            "📈 Daily Change",
                            f"{stats['daily_change_pct']:+.2f}%",
                            delta=f"${stats['daily_change']:+.2f}"
                        )
                    
                    # Company info
                    st.subheader(f"🏢 {company_info['name']}")
                    st.write(f"**Sector:** {company_info['sector']}")
                    
                    # Safely handle market_cap which might be None
                    market_cap = company_info.get('market_cap', 0) or 0
                    if market_cap > 0:
                        st.write(f"**Market Cap:** {format_market_cap(market_cap)}")
                    
                    # Key metrics
                    st.subheader("📊 Key Metrics")
                    
                    metric_col1, metric_col2 = st.columns(2)
                    
                    with metric_col1:
                        st.metric("📈 52-Week High", format_price(stats['high_52w']))
                        # RSI with explanation tooltip
                        # st.metric("🎯 RSI(14)", f"{rsi:.1f}", help="Relative Strength Index: Momentum indicator (0-100). Values >70 suggest overbought, <30 suggest oversold.")
                        # st.metric("📊 Historical Volatility", f"{volatility:.1f}%", help="30-day annualized volatility showing price movement consistency")
                    
                    with metric_col2:
                        st.metric("📉 52-Week Low", format_price(stats['low_52w']))
                        # st.metric("🔄 Avg Volume", format_volume(stats['volume_avg']))
                        # Empty space where SMA was
                    
                    # Trend signal
                    # trend_class = trend_signal.lower().replace('overbought', 'neutral').replace('oversold', 'neutral')
                    # st.markdown(f"""
                    # <div class="metric-card">
                    #     <h4>🎯 Trend Signal</h4>
                    #     <p class="{trend_class}">{trend_emoji} {trend_signal.title()}</p>
                    # </div>
                    # """, unsafe_allow_html=True)
                    
                    # Simple indicators
                    st.subheader("🚦 Technical Indicators")
                    
                    # RSI status with detailed explanation
                    # if rsi > 70:
                    #     rsi_status = "🔴 Overbought (May decline)"
                    #     rsi_explanation = "RSI above 70 suggests the stock may be overbought and due for a pullback."
                    # elif rsi < 30:
                    #     rsi_status = "🟢 Oversold (May recover)"
                    #     rsi_explanation = "RSI below 30 suggests the stock may be oversold and due for a bounce."
                    # else:
                    #     rsi_status = "🟡 Neutral"
                    #     rsi_explanation = "RSI between 30-70 indicates balanced momentum without extreme conditions."
                    # 
                    # st.write(f"**RSI Status:** {rsi_status}")
                    # st.caption(rsi_explanation)
                    
                    # 52-week position
                    price_range = stats['high_52w'] - stats['low_52w']
                    if price_range > 0:
                        position_pct = ((stats['current_price'] - stats['low_52w']) / price_range) * 100
                        st.write(f"**52-Week Position:** {position_pct:.1f}% of range")
                        
                        if position_pct > 80:
                            range_status = "🔴 Near 52-week high"
                        elif position_pct < 20:
                            range_status = "🟢 Near 52-week low"
                        else:
                            range_status = "🟡 Mid-range"
                        
                        st.write(f"**Range Status:** {range_status}")
                    
                    # Store data in session state for chat
                    st.session_state['current_ticker'] = ticker
                    st.session_state['current_stats'] = stats
                    st.session_state['current_df'] = df
                
            else:
                st.error(f"❌ Invalid ticker symbol: {ticker}")
                st.session_state.pop('current_ticker', None)
    
    with col2:
        st.header("📈 Price Chart & Analysis")
        
        if 'current_df' in st.session_state:
            df = st.session_state['current_df']
            ticker = st.session_state['current_ticker']
            
            # Create price chart
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['Close'],
                mode='lines',
                name='Price',
                line=dict(color='#667eea', width=2)
            ))
            
            # Chart shows price only (SMA removed per user request)
            
            # Update layout
            fig.update_layout(
                title=f"{ticker} - 30 Day Price Chart",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                template="plotly_white",
                height=400
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # Volume chart
            vol_fig = go.Figure()
            vol_fig.add_trace(go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color='lightblue'
            ))
            
            vol_fig.update_layout(
                title=f"{ticker} - Trading Volume",
                xaxis_title="Date", 
                yaxis_title="Volume",
                template="plotly_white",
                height=200,
                showlegend=False
            )
            
            st.plotly_chart(vol_fig, width='stretch')
        
        else:
            st.info("👆 Enter a ticker symbol to see charts and analysis")
    
    # AI Chat Interface
    st.header("🤖 AI Market Assistant")
    
    if 'current_ticker' in st.session_state and llm_provider:
        ticker = st.session_state['current_ticker']
        stats = st.session_state['current_stats']
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state['chat_history'] = []
        
        # Clear chat when ticker changes
        if st.session_state.get('last_chat_ticker') != ticker:
            st.session_state['chat_history'] = []
            st.session_state['last_chat_ticker'] = ticker
        
        col_chat1, col_chat2 = st.columns([3, 1])
        
        with col_chat1:
            # Preset questions
            st.subheader("💭 Quick Questions")
            preset_questions = get_preset_questions()
            
            question_cols = st.columns(4)
            for i, (display_text, question) in enumerate(preset_questions.items()):
                with question_cols[i % 4]:
                    if st.button(display_text, key=f"preset_{i}"):
                        # Add to chat and get response
                        st.session_state['chat_history'].append({"role": "user", "content": question})
                        
                        with st.spinner("🤖 Thinking..."):
                            response = generate_response(ticker, stats, question, llm_provider)
                            formatted_response = format_llm_response(response)
                        
                        st.session_state['chat_history'].append({"role": "assistant", "content": formatted_response})
                        st.rerun()
        
        # Telegram section moved to sidebar
        
        # Custom question input - use form to prevent rerun on every keystroke
        with st.form(key="chat_form", clear_on_submit=True):
            user_question = st.text_input(
                "💬 Ask about this stock:",
                placeholder=f"e.g., What do you think about {ticker}'s current valuation?",
                key="user_input"
            )
            submit_button = st.form_submit_button("Send 💬")
        
        if submit_button and user_question:
            # Add user question to chat
            st.session_state['chat_history'].append({"role": "user", "content": user_question})
            
            # Generate AI response
            with st.spinner("🤖 Analyzing..."):
                response = generate_response(ticker, stats, user_question, llm_provider)
                formatted_response = format_llm_response(response)
            
            st.session_state['chat_history'].append({"role": "assistant", "content": formatted_response})
            st.rerun()
        
        # Display chat history
        if st.session_state.get('chat_history'):
            st.subheader(f"💬 Chat History - {ticker}")
            
            for message in st.session_state['chat_history']:
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message">
                        <strong>👤 You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ai-response">
                        <strong>🤖 AI Assistant:</strong><br>
                        {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Clear chat button
            if st.button("🗑️ Clear Chat History"):
                st.session_state['chat_history'] = []
                st.rerun()
    
    elif not llm_provider:
        st.warning("⚠️ Please configure at least one AI provider in your .env file to use the chat feature.")
    else:
        st.info("👆 Select a ticker to start chatting with the AI assistant")
    
    # Footer
    st.divider()
    st.markdown("---")
    
    col_footer1, col_footer2, col_footer3 = st.columns(3)
    
    with col_footer1:
        st.write("📊 **AI Market Chat Companion**")
        st.write("Interactive market analysis tool")
    
    with col_footer2:
        st.write("🔗 **Data Sources**")
        st.write("Yahoo Finance • AI Analysis")
    
    with col_footer3:
        st.write("⚠️ **Disclaimer**")
        st.write("Educational use only. Not financial advice.")


if __name__ == "__main__":
    main()