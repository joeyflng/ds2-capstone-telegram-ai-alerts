"""
LLM integration utilities for AI Market Chat Companion
Supports Gemini, OpenAI, and Groq for AI-powered market analysis
"""
import os
from typing import Dict, Optional
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_api_key(key_name: str) -> Optional[str]:
    """
    Get API key from Hugging Face Spaces secrets or environment variables.
    Prioritizes st.secrets (HF Spaces) over os.environ (local).
    """
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name)

# LLM Imports with error handling
GEMINI_AVAILABLE = False
OPENAI_AVAILABLE = False
GROQ_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = bool(get_api_key("GOOGLE_API_KEY"))
    if GEMINI_AVAILABLE:
        genai.configure(api_key=get_api_key("GOOGLE_API_KEY"))
except ImportError:
    pass

try:
    import openai
    OPENAI_AVAILABLE = bool(get_api_key("OPENAI_API_KEY"))
    if OPENAI_AVAILABLE:
        openai.api_key = get_api_key("OPENAI_API_KEY")
except ImportError:
    pass

try:
    from groq import Groq
    GROQ_AVAILABLE = bool(get_api_key("GROQ_API_KEY"))
except ImportError:
    pass


def get_available_providers() -> Dict[str, bool]:
    """Get status of available LLM providers"""
    return {
        'gemini': GEMINI_AVAILABLE,
        'openai': OPENAI_AVAILABLE,
        'groq': GROQ_AVAILABLE
    }


def generate_response_gemini(ticker: str, stats: Dict, user_question: str) -> str:
    """
    Generate response using Google Gemini
    
    Args:
        ticker: Stock symbol
        stats: Market statistics dictionary
        user_question: User's question about the stock
    
    Returns:
        str: AI-generated response
    """
    if not GEMINI_AVAILABLE:
        return "❌ Gemini API not available. Please configure GOOGLE_API_KEY."
    
    try:
        # Create market context
        context = create_market_context(ticker, stats)
        
        # Create prompt
        prompt = f"""
You are a professional financial analyst.

Stock: {ticker}

Market Data:
{context}

Question: {user_question}

Answer the question exactly as asked. If a specific length is requested (e.g., "in 20 words"), strictly follow it. This is educational analysis only, not financial advice.
"""
        
        # Use Gemini 2.5 Flash
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        return f"❌ Gemini API Error: {str(e)}"


def generate_response_openai(ticker: str, stats: Dict, user_question: str) -> str:
    """
    Generate response using OpenAI
    
    Args:
        ticker: Stock symbol
        stats: Market statistics dictionary
        user_question: User's question about the stock
    
    Returns:
        str: AI-generated response
    """
    if not OPENAI_AVAILABLE:
        return "❌ OpenAI API not available. Please configure OPENAI_API_KEY."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=get_api_key("OPENAI_API_KEY"))
        
        # Create market context
        context = create_market_context(ticker, stats)
        
        # Create messages
        messages = [
            {
                "role": "system",
                "content": "You are a professional financial analyst. Provide accurate, helpful market insights. Follow the user's specific instructions on response length and format. Always include appropriate risk disclaimers. This is educational analysis only, not financial advice."
            },
            {
                "role": "user", 
                "content": f"""
Stock: {ticker}

Market Data:
{context}

Question: {user_question}

Answer the question exactly as asked. If a specific length is requested (e.g., "in 20 words"), strictly follow it.
"""
            }
        ]
        
        # Generate response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=800,  # Increased for complete responses
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"❌ OpenAI API Error: {str(e)}"


def generate_response_groq(ticker: str, stats: Dict, user_question: str) -> str:
    """
    Generate response using Groq
    
    Args:
        ticker: Stock symbol
        stats: Market statistics dictionary
        user_question: User's question about the stock
    
    Returns:
        str: AI-generated response
    """
    if not GROQ_AVAILABLE:
        return "❌ Groq API not available. Please configure GROQ_API_KEY."
    
    try:
        client = Groq(api_key=get_api_key("GROQ_API_KEY"))
        
        # Create market context
        context = create_market_context(ticker, stats)
        
        # Create messages
        messages = [
            {
                "role": "system",
                "content": """You are a professional financial analyst providing market insights. 

Key guidelines:
- Follow the user's specific instructions on response length and format (e.g., if they ask for 20 words, provide exactly that)
- Be accurate and data-driven
- Always include risk disclaimers unless the response is very brief
- Use bullet points for clarity when appropriate
- Focus on the specific question asked
- This is educational analysis only, not financial advice

Your expertise: Technical analysis, market trends, risk assessment, and data interpretation."""
            },
            {
                "role": "user",
                "content": f"""
Stock: {ticker}

Market Data:
{context}

Question: {user_question}

Answer the question exactly as asked. If a specific length is requested (e.g., "in 20 words"), strictly follow it.
"""
            }
        ]
        
        # Generate response with optimized settings for Llama
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Fastest Groq model
            messages=messages,
            max_tokens=1000,  # Increased for complete responses
            temperature=0.3,  # Balanced creativity/accuracy
            top_p=0.9,       # Focus on most likely tokens
            stream=False     # Full response for web UI
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"❌ Groq API Error: {str(e)}"


def generate_response(ticker: str, stats: Dict, user_question: str, provider: str = None) -> str:
    """
    Generate AI response using the specified or best available provider
    
    Args:
        ticker: Stock symbol
        stats: Market statistics dictionary  
        user_question: User's question about the stock
        provider: Preferred provider ('gemini', 'openai', 'groq') or None for auto
    
    Returns:
        str: AI-generated response
    """
    # Auto-select provider if not specified (prioritize Groq)
    if provider is None:
        provider = get_api_key("DEFAULT_LLM_PROVIDER") or "groq"
    
    # Try specified provider first
    if provider == "groq" and GROQ_AVAILABLE:
        return generate_response_groq(ticker, stats, user_question)
    elif provider == "gemini" and GEMINI_AVAILABLE:
        return generate_response_gemini(ticker, stats, user_question)
    elif provider == "openai" and OPENAI_AVAILABLE:
        return generate_response_openai(ticker, stats, user_question)
    
    # Fallback to any available provider (prioritize Groq)
    if GROQ_AVAILABLE:
        return generate_response_groq(ticker, stats, user_question)
    elif GEMINI_AVAILABLE:
        return generate_response_gemini(ticker, stats, user_question)
    elif OPENAI_AVAILABLE:
        return generate_response_openai(ticker, stats, user_question)
    
    # No providers available
    return """❌ No LLM providers configured. 

🚀 **Quick Setup for Groq (Recommended - Free & Fast):**
1. Get free API key: https://console.groq.com/keys
2. Add to .env file: GROQ_API_KEY=your_groq_key_here
3. Restart the app

💡 **Why Groq?**
- ✅ Completely FREE tier with generous limits
- ⚡ Ultra-fast Llama 3.1 responses  
- 🔓 No credit card required
- 📊 Perfect for market analysis

**Alternative providers** (if you have keys):
- GOOGLE_API_KEY for Gemini
- OPENAI_API_KEY for OpenAI

Check the .env.example file for setup instructions."""


def create_market_context(ticker: str, stats: Dict) -> str:
    """
    Create formatted market context for LLM prompts
    
    Args:
        ticker: Stock symbol
        stats: Market statistics dictionary
    
    Returns:
        str: Formatted context string
    """
    if not stats:
        return f"No market data available for {ticker}."
    
    try:
        context = f"""
Stock: {ticker}
Current Price: ${stats.get('current_price', 0):.2f}
Daily Change: {stats.get('daily_change_pct', 0):+.2f}%
30-Day High: ${stats.get('high_30d', 0):.2f}
30-Day Low: ${stats.get('low_30d', 0):.2f}
RSI(14): {stats.get('rsi', 50):.1f}
SMA(20): ${stats.get('sma20', 0):.2f}
Volatility: {stats.get('volatility', 0):.1f}%
Trend Signal: {stats.get('trend_signal', 'neutral')} {stats.get('trend_emoji', '🟡')}
Data Points: {stats.get('data_points', 0)} days
"""
        
        return context.strip()
    
    except Exception:
        return f"Error formatting market context for {ticker}."


def get_preset_questions() -> Dict[str, str]:
    """Get preset questions for the chat interface"""
    return {
        "📊 What's the short-term trend?": "What is the short-term trend based on recent price action?",
        "📈 Analyze the momentum": "Explain the current momentum and what it indicates",
        "🎯 Risk assessment": "What are the key risks I should be aware of?",
        "💡 Key insights": "What are the most important insights from this data?",
        "🔮 Technical outlook": "What does the technical analysis suggest?",
        "⚖️ Volatility analysis": "How volatile is this stock and what does it mean?",
        "🎪 Market context": "How does this stock fit in the current market environment?",
        "📋 Summary": "Give me a brief overall summary of this stock"
    }


def format_llm_response(response: str) -> str:
    """
    Format LLM response for better display in Streamlit
    
    Args:
        response: Raw LLM response
    
    Returns:
        str: Formatted response
    """
    if response.startswith("❌"):
        return response
    
    # Add disclaimer if not present
    if "not financial advice" not in response.lower():
        response += "\n\n⚠️ *This analysis is for educational purposes only and is not financial advice.*"
    
    return response


def test_llm_connectivity() -> Dict[str, str]:
    """
    Test connectivity to all available LLM providers
    
    Returns:
        dict: Status of each provider
    """
    results = {}
    
    # Test Gemini
    if GEMINI_AVAILABLE:
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content("Hello, respond with 'Gemini OK'")
            results['gemini'] = "✅ Connected"
        except Exception as e:
            results['gemini'] = f"❌ Error: {str(e)}"
    else:
        results['gemini'] = "❌ API key not configured"
    
    # Test Groq
    if GROQ_AVAILABLE:
        try:
            client = Groq(api_key=get_api_key("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Hello, respond with 'Groq OK'"}],
                max_tokens=10
            )
            results['groq'] = "✅ Connected"
        except Exception as e:
            results['groq'] = f"❌ Error: {str(e)}"
    else:
        results['groq'] = "❌ API key not configured"
    
    # Test OpenAI
    if OPENAI_AVAILABLE:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=get_api_key("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello, respond with 'OpenAI OK'"}],
                max_tokens=10
            )
            results['openai'] = "✅ Connected"
        except Exception as e:
            results['openai'] = f"❌ Error: {str(e)}"
    else:
        results['openai'] = "❌ API key not configured"
    
    return results