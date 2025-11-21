"""
AI Research service module for LLM-powered company analysis
"""
import requests
# import yfinance as yf  # Replaced with rate-limited yahoo_direct

# Import rate-limited Yahoo Finance functions
try:
    from .yahoo_direct import get_yahoo_quote, get_yahoo_company_info
except ImportError:
    from yahoo_direct import get_yahoo_quote, get_yahoo_company_info

# Handle config imports with fallbacks
try:
    from config import GROQ_API_KEY, GROQ_MODEL, STOCKS_TO_CHECK
except ImportError:
    try:
        from ..config import GROQ_API_KEY, GROQ_MODEL, STOCKS_TO_CHECK
    except ImportError:
        import os
        GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        STOCKS_TO_CHECK = ["AAPL", "MSFT", "GOOGL"]

# Groq LLM Integration
try:
    from groq import Groq
    GROQ_AVAILABLE = bool(GROQ_API_KEY)
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ Groq not installed. Install with: pip install groq")


def format_number(num):
    """Format number for display"""
    if num is None or num == 'N/A':
        return 'N/A'
    try:
        if num >= 1e9:
            return f"{num/1e9:.1f}B"
        elif num >= 1e6:
            return f"{num/1e6:.1f}M"
        elif num >= 1e3:
            return f"{num/1e3:.1f}K"
        else:
            return f"{num:,.0f}"
    except:
        return str(num)


def format_metric(value):
    """Format financial metric for display"""
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        return f"{float(value):.2f}"
    except:
        return str(value)


def format_percentage(value):
    """Format percentage for display"""
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        return f"{float(value)*100:.1f}%"
    except:
        return str(value)


def groq_chat(system_prompt: str, user_prompt: str) -> str:
    """Send a query to Groq LLM and get response"""
    if not GROQ_AVAILABLE:
        return "❌ Groq LLM not available. Install with: pip install groq"
    
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY not set in .env file"
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL or "llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ LLM Error: {e}"


def get_company_fundamentals(symbol):
    """Get company fundamental data using hybrid FMP+Yahoo system"""
    try:
        print(f"📊 Getting company fundamentals for {symbol} via hybrid API...")
        
        # Try to import hybrid system first
        try:
            from .fmp_hybrid import get_hybrid_stock_quote, get_hybrid_company_fundamentals
            
            # Get basic quote data using hybrid
            quote_data = get_hybrid_stock_quote(symbol)
            if not quote_data:
                print(f"⚠️ No quote data available for {symbol}")
                return None
            
            # Get detailed company fundamentals using hybrid
            company_info = get_hybrid_company_fundamentals(symbol)
            if company_info:
                print(f"✅ Got comprehensive fundamentals for {symbol}")
                # Restructure FMP hybrid response to match expected format
                # Convert FMP metrics/ratios lists to dict format
                metrics_list = company_info.get('metrics', [])
                ratios_list = company_info.get('ratios', [])
                
                # Extract first item (most recent) from lists if available
                latest_metrics = metrics_list[0] if metrics_list and len(metrics_list) > 0 else {}
                latest_ratios = ratios_list[0] if ratios_list and len(ratios_list) > 0 else {}
                
                fundamentals = {
                    'profile': {
                        'companyName': company_info.get('companyName', symbol),
                        'sector': company_info.get('sector', 'N/A'),
                        'industry': company_info.get('industry', 'N/A'),
                        'description': company_info.get('description', 'N/A'),
                        'marketCap': company_info.get('marketCap', 0)
                    },
                    'metrics': {
                        'pe_ratio': latest_metrics.get('peRatio') or latest_ratios.get('priceEarningsRatio'),
                        'price_to_book': latest_ratios.get('priceToBookRatio'),
                        'price_to_sales': latest_ratios.get('priceToSalesRatio'),
                        'roe': latest_ratios.get('returnOnEquity'),
                        'roa': latest_ratios.get('returnOnAssets'),
                        'gross_margin': latest_ratios.get('grossProfitMargin'),
                        'operating_margin': latest_ratios.get('operatingProfitMargin'),
                        'profit_margin': latest_ratios.get('netProfitMargin'),
                        'debt_to_equity': latest_ratios.get('debtEquityRatio'),
                        'current_ratio': latest_ratios.get('currentRatio'),
                        'revenue_growth': latest_metrics.get('revenuePerShare')
                    },
                    'current_price': quote_data.get('price', 0),
                    'change': quote_data.get('change', 0),
                    'change_percent': quote_data.get('changePercent', 0),
                    'volume': quote_data.get('volume', 0),
                    'day_high': quote_data.get('dayHigh', 0),
                    'day_low': quote_data.get('dayLow', 0),
                    'week_52_high': quote_data.get('week52High', 0),
                    'week_52_low': quote_data.get('week52Low', 0),
                    'source': company_info.get('source', 'hybrid')
                }
                return fundamentals
            else:
                print(f"⚠️ No detailed fundamentals, using basic quote data")
                # Return basic info from quote if detailed info fails
                return {
                    'symbol': symbol.upper(),
                    'companyName': quote_data.get('companyName', symbol),
                    'sector': 'N/A',
                    'industry': 'N/A', 
                    'description': 'N/A',
                    'marketCap': quote_data.get('marketCap', 0),
                    'source': quote_data.get('source', 'hybrid')
                }
                
        except ImportError:
            print(f"⚠️ Hybrid system not available, falling back to Yahoo...")
            
            # Get basic quote data
            quote_data = get_yahoo_quote(symbol)
            if not quote_data:
                print(f"⚠️ No quote data available for {symbol}")
                return None
            
            # Get detailed company info
            company_info = get_yahoo_company_info(symbol)
            if not company_info:
                print(f"⚠️ No company info available for {symbol}")
                # Return basic info from quote if detailed info fails
                return {
                    'profile': {
                        'companyName': quote_data.get('companyName', symbol),
                        'sector': 'N/A',
                        'industry': 'N/A', 
                        'description': 'N/A',
                        'marketCap': quote_data.get('marketCap', 0),
                        'employees': 0,
                        'country': 'N/A',
                        'website': 'N/A'
                },
                'metrics': {
                    'pe_ratio': None,
                    'forward_pe': None,
                    'peg_ratio': None,
                    'price_to_book': None,
                    'price_to_sales': None,
                    'profit_margins': None,
                    'revenue_growth': None,
                    'return_on_equity': None,
                    'debt_to_equity': None,
                    'current_ratio': None
                },
                'current_price': quote_data.get('price', 0),
                'change': quote_data.get('change', 0),
                'change_percent': quote_data.get('changePercent', 0),
                'volume': quote_data.get('volume', 0)
            }
        
        # Combine quote and company data
        fundamentals = {
            'profile': company_info['profile'],
            'metrics': company_info['metrics'],
            'financial_data': company_info.get('financial_data', {}),
            'current_price': quote_data.get('price', 0),
            'change': quote_data.get('change', 0),
            'change_percent': quote_data.get('changePercent', 0),
            'volume': quote_data.get('volume', 0),
            'day_high': quote_data.get('dayHigh', 0),
            'day_low': quote_data.get('dayLow', 0),
            'week_52_high': quote_data.get('week52High', 0),
            'week_52_low': quote_data.get('week52Low', 0)
        }
        
        print(f"✅ Retrieved fundamentals for {symbol}: {company_info['profile']['companyName']}")
        return fundamentals
        
    except Exception as e:
        print(f"❌ Error getting company fundamentals for {symbol}: {e}")
        return None


def format_company_data_for_llm(symbol, company_data, stock_quote=None):
    """Format company data into a comprehensive text for LLM analysis"""
    if not company_data:
        return f"No fundamental data available for {symbol}"
    
    profile = company_data.get('profile', {})
    metrics = company_data.get('metrics', {})
    
    # Build comprehensive company data text
    data_text = f"""
COMPANY: {profile.get('companyName', symbol)} ({symbol})
SECTOR: {profile.get('sector', 'N/A')}
INDUSTRY: {profile.get('industry', 'N/A')}
DESCRIPTION: {profile.get('description', 'N/A')[:500]}...

COMPANY SIZE:
- Market Cap: {format_number(profile.get('marketCap', 0))}
- Employees: {format_number(profile.get('employees', 0))}
- Country: {profile.get('country', 'N/A')}

VALUATION METRICS:
- P/E Ratio: {format_metric(metrics.get('pe_ratio'))}
- Forward P/E: {format_metric(metrics.get('forward_pe'))}
- PEG Ratio: {format_metric(metrics.get('peg_ratio'))}
- Price-to-Book: {format_metric(metrics.get('price_to_book'))}
- Price-to-Sales: {format_metric(metrics.get('price_to_sales'))}

PROFITABILITY:
- Return on Equity: {format_percentage(metrics.get('roe'))}
- Return on Assets: {format_percentage(metrics.get('roa'))}
- Gross Margin: {format_percentage(metrics.get('gross_margin'))}
- Operating Margin: {format_percentage(metrics.get('operating_margin'))}
- Profit Margin: {format_percentage(metrics.get('profit_margin'))}

FINANCIAL HEALTH:
- Debt-to-Equity: {format_metric(metrics.get('debt_to_equity'))}
- Current Ratio: {format_metric(metrics.get('current_ratio'))}
- Quick Ratio: {format_metric(metrics.get('quick_ratio'))}
"""
    
    if stock_quote:
        data_text += f"""
CURRENT STOCK DATA:
- Current Price: ${stock_quote.get('price', 'N/A')}
- Market Cap: ${stock_quote.get('marketCap', 'N/A')}
- 52-Week High: ${stock_quote.get('yearHigh', 'N/A')}
- 52-Week Low: ${stock_quote.get('yearLow', 'N/A')}
- Volume: {stock_quote.get('volume', 'N/A')}
"""
    
    return data_text


def get_analysis_system_prompts():
    """Get system prompts for different analysis types"""
    return {
        "brief": """You are a financial analyst providing a brief company summary. 
        Give a concise overview in 3-4 paragraphs covering:
        1. What the company does (business model)
        2. Key market position and main competitors
        3. Recent financial highlights (if data available)
        4. Main strengths or growth drivers
        Keep it under 300 words, accessible to general investors. This is educational, not financial advice.""",
        
        "overview": """You are a professional financial analyst providing comprehensive company research. 
        Analyze the provided company data and give an objective overview covering:
        1. Business model and competitive position
        2. Financial health and key metrics analysis
        3. Recent performance trends
        4. Key strengths and concerns
        Keep analysis factual, balanced, and under 1000 words. This is not financial advice.""",
        
        "investment": """You are an investment research analyst. Based on the company data provided, analyze:
        1. Investment thesis (bull and bear cases)
        2. Valuation assessment using provided metrics
        3. Growth prospects and catalysts
        4. Major risks and concerns
        5. Technical analysis summary if relevant
        Provide objective analysis. Clearly state this is not financial advice and encourage due diligence.""",
        
        "risks": """You are a risk analyst. Focus on identifying and analyzing risks for this company:
        1. Financial risks (debt, cash flow, margins)
        2. Market and competitive risks
        3. Regulatory and industry risks
        4. Operational risks
        5. Risk mitigation strategies
        Be comprehensive but concise. This is educational analysis, not financial advice.""",
        
        "financials": """You are a financial analyst specializing in company financial health. Deep dive into:
        1. Balance sheet strength and weaknesses
        2. Profitability analysis and trends
        3. Cash flow analysis
        4. Financial ratios interpretation
        5. Debt and liquidity analysis
        Use the provided financial data and ratios. Keep technical but accessible.""",
        
        "comparison": """You are an industry analyst. Based on the provided data, analyze how this company compares to industry standards:
        1. Market position vs competitors
        2. Financial metrics vs industry averages
        3. Growth trajectory comparison
        4. Competitive advantages/disadvantages
        5. Investment attractiveness relative to peers
        Provide context on industry trends and this company's position."""
    }


def research_company(symbol, query_type="overview"):
    """
    Research a company using LLM with real financial data
    
    query_type options:
    - "brief": Short company summary (3-4 paragraphs, under 300 words)
    - "overview": General company analysis (comprehensive, under 1000 words)
    - "investment": Investment analysis and recommendation
    - "risks": Risk analysis
    - "comparison": Compare with industry peers
    - "financials": Deep dive into financial health
    """
    from services.data_providers import get_stock_quote  # Import here to avoid circular imports
    import config  # Import config to get fresh STOCKS_TO_CHECK
    
    print(f"🔍 Researching {symbol} - {query_type}...")
    
    # Validate symbol is in our monitored list (reload from config to get latest)
    current_stocks = config.STOCKS_TO_CHECK
    if symbol not in current_stocks:
        return f"❌ {symbol} is not in the monitored stock list. Current stocks: {', '.join(current_stocks)}"
    
    # Get real-time stock data
    stock_quote = get_stock_quote(symbol)
    
    # Get fundamental company data
    company_data = get_company_fundamentals(symbol)
    
    # Format data for LLM
    company_info = format_company_data_for_llm(symbol, company_data, stock_quote)
    
    # Get system prompt based on query type
    system_prompts = get_analysis_system_prompts()
    system_prompt = system_prompts.get(query_type, system_prompts["overview"])
    
    user_prompt = f"""
Please analyze {symbol} based on the following real company data:

{company_info}

Focus on {query_type} analysis. Be specific, use the actual numbers provided, and give actionable insights.
"""
    
    # Get LLM analysis
    analysis = groq_chat(system_prompt, user_prompt)
    
    return analysis


def brief_company_summary_with_telegram(symbol):
    """Get brief company summary and send to Telegram"""
    from core.telegram_client import send_telegram_message  # Import here to avoid circular imports
    
    try:
        analysis = research_company(symbol, query_type="brief")
        
        # Create header message for brief summary
        header = f"📋 *BRIEF SUMMARY: {symbol}*\n" + "="*30 + "\n\n"
        full_message = header + analysis
        
        # Send to Telegram (brief, so use regular message)
        send_telegram_message(full_message)
        
        print(f"✅ Brief summary for {symbol} sent to Telegram")
        return True
        
    except Exception as e:
        from core.telegram_client import send_telegram_message
        error_msg = f"❌ Error getting brief summary for {symbol}: {e}"
        send_telegram_message(error_msg)
        print(error_msg)
        return False


def research_company_with_telegram(symbol, query_type="overview"):
    """Research company and send results to Telegram"""
    from core.telegram_client import send_long_message  # Import here to avoid circular imports
    
    try:
        analysis = research_company(symbol, query_type)
        
        # Create header message
        header = f"🔍 *{query_type.upper()} ANALYSIS: {symbol}*\n" + "="*40 + "\n\n"
        full_message = header + analysis
        
        # Send to Telegram using long message handler
        send_long_message(full_message)
        
        print(f"✅ Company research for {symbol} sent to Telegram")
        return True
        
    except Exception as e:
        from core.telegram_client import send_telegram_message
        error_msg = f"❌ Error researching {symbol}: {e}"
        send_telegram_message(error_msg)
        print(error_msg)
        return False