#!/usr/bin/env python3
"""
Setup verification script for AI Market Chat Companion
Run this to test your installation and API connections
"""
import os
import sys
from dotenv import load_dotenv

def main():
    print("📊 AI Market Chat Companion - Setup Verification")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Check Python version
    print(f"🐍 Python Version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")
    
    print("\n📦 Checking Dependencies...")
    
    # Check core dependencies
    try:
        import streamlit
        print(f"✅ Streamlit: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not installed - run: pip install streamlit")
        return False
    
    try:
        import yfinance
        print(f"✅ yfinance: {yfinance.__version__}")
    except ImportError:
        print("❌ yfinance not installed - run: pip install yfinance")
        return False
    
    try:
        import plotly
        print(f"✅ Plotly: {plotly.__version__}")
    except ImportError:
        print("❌ Plotly not installed - run: pip install plotly")
        return False
    
    try:
        import pandas
        print(f"✅ Pandas: {pandas.__version__}")
    except ImportError:
        print("❌ Pandas not installed")
        return False
    
    print("\n🔐 Checking API Configuration...")
    
    # Check API keys
    api_keys = {
        'GOOGLE_API_KEY': 'Gemini',
        'GROQ_API_KEY': 'Groq', 
        'OPENAI_API_KEY': 'OpenAI'
    }
    
    configured_providers = 0
    for env_var, provider in api_keys.items():
        if os.getenv(env_var):
            print(f"✅ {provider} API key configured")
            configured_providers += 1
        else:
            print(f"⚠️  {provider} API key not configured")
    
    if configured_providers == 0:
        print("❌ No AI providers configured - check your .env file")
        return False
    else:
        print(f"✅ {configured_providers} AI provider(s) configured")
    
    print("\n🧪 Testing Market Data...")
    
    # Test market data
    try:
        from utils.market import fetch_prices, validate_ticker
        
        # Test ticker validation
        if validate_ticker('AAPL'):
            print("✅ Market data access working")
        else:
            print("❌ Market data access failed")
            return False
            
    except Exception as e:
        print(f"❌ Market data test failed: {e}")
        return False
    
    print("\n🤖 Testing AI Integration...")
    
    # Test AI providers
    try:
        from utils.llm import test_llm_connectivity
        
        results = test_llm_connectivity()
        working_providers = 0
        
        for provider, status in results.items():
            if "✅" in status:
                print(f"✅ {provider.title()} AI working")
                working_providers += 1
            else:
                print(f"❌ {provider.title()}: {status}")
        
        if working_providers == 0:
            print("❌ No AI providers working")
            return False
        
    except Exception as e:
        print(f"⚠️  AI test error: {e}")
    
    print("\n🎉 Setup Verification Complete!")
    print("=" * 50)
    print("🚀 Ready to run: streamlit run app.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)