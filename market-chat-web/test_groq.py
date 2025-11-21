"""
Test script for Groq LLM functionality
Make sure you have GROQ_API_KEY in your .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_groq_connectivity():
    """Test Groq API connectivity"""
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        print("❌ GROQ_API_KEY not found in environment")
        print("📝 Please add GROQ_API_KEY to your .env file")
        return False
    
    try:
        from groq import Groq
        print("✅ Groq package imported successfully")
        
        # Test API connection
        client = Groq(api_key=groq_key)
        
        # Simple test message
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "Hello, please respond with 'Groq API working!'"}
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        print(f"✅ Groq API Response: {result}")
        
        return True
        
    except ImportError:
        print("❌ Groq package not installed")
        print("📦 Run: pip install groq")
        return False
    
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return False

def test_market_analysis():
    """Test market analysis with Groq"""
    if not test_groq_connectivity():
        return False
    
    try:
        from groq import Groq
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Sample market data
        sample_data = """
Stock: AAPL
Current Price: $272.95
Daily Change: -0.19%
30-Day High: $277.05
30-Day Low: $243.76
RSI(14): 72.6
SMA(20): $265.50
Volatility: 15.2%
Trend Signal: neutral 🟡
"""
        
        # Test market analysis prompt
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional financial analyst. Provide helpful market insights in under 200 words. Always include risk disclaimers."
                },
                {
                    "role": "user", 
                    "content": f"Analyze this stock data and provide key insights:\n\n{sample_data}\n\nWhat's the short-term outlook?"
                }
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content
        print("🤖 Sample Market Analysis:")
        print("=" * 50)
        print(analysis)
        print("=" * 50)
        print("✅ Market analysis test successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Market analysis test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Groq LLM Integration")
    print("=" * 50)
    
    # Test connectivity
    print("1️⃣ Testing Groq API connectivity...")
    connectivity_ok = test_groq_connectivity()
    
    if connectivity_ok:
        print("\n2️⃣ Testing market analysis...")
        analysis_ok = test_market_analysis()
        
        if analysis_ok:
            print("\n🎉 All Groq tests passed!")
            print("✅ Ready to use Groq for market analysis")
        else:
            print("\n⚠️ API works but analysis failed")
    else:
        print("\n❌ Please check your Groq API setup")
        print("\n📋 Setup steps:")
        print("1. Get free API key from https://console.groq.com/keys")
        print("2. Add GROQ_API_KEY=your_key to .env file")
        print("3. Run: pip install groq")