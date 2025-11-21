"""
Market Sentiment Calculator
Calculates a custom Fear & Greed Index (0-100) using FMP indicators.

Components (each 25%):
1. VIX Level - Volatility/Fear indicator
2. S&P 500 Momentum - Position vs 52-week range
3. Safe Haven Demand - Treasury yields direction
4. Market Breadth - Advancing vs Declining stocks
"""

import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_DELAY_SECONDS = float(os.getenv("FMP_DELAY_SECONDS", "5"))


def get_vix_score() -> Tuple[Optional[float], Optional[Dict]]:
    """
    Get VIX-based fear score (0-100).
    Calibrated to CNN Fear & Greed Index standards:
    VIX < 12: Extreme Greed (100)
    VIX 12-17: Greed (75)
    VIX 17-24: Neutral (50)
    VIX 24-35: Fear (25)
    VIX > 35: Extreme Fear (0)
    
    Returns: (score, details_dict)
    """
    try:
        url = f'https://financialmodelingprep.com/api/v3/quote/^VIX?apikey={FMP_API_KEY}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"VIX fetch failed: {response.status_code}")
            return None, None
            
        data = response.json()
        if not data:
            return None, None
            
        vix_value = data[0].get('price', 0)
        change_pct = data[0].get('changesPercentage', 0)
        
        # Calculate score (inverse relationship - higher VIX = more fear = lower score)
        # Recalibrated to match CNN Fear & Greed thresholds
        if vix_value < 12:
            score = 100
            interpretation = "Extreme Greed"
        elif vix_value < 17:
            score = 75 + ((17 - vix_value) / 5) * 25  # Linear interpolation 75-100
            interpretation = "Greed"
        elif vix_value < 24:
            score = 50 + ((24 - vix_value) / 7) * 25  # Linear interpolation 50-75
            interpretation = "Neutral"
        elif vix_value < 35:
            score = 25 + ((35 - vix_value) / 11) * 25  # Linear interpolation 25-50
            interpretation = "Fear"
        else:
            score = max(0, 25 - ((vix_value - 35) / 15) * 25)  # Below 0 capped at 0
            interpretation = "Extreme Fear"
            
        details = {
            'value': vix_value,
            'change_pct': change_pct,
            'interpretation': interpretation,
            'component': 'VIX'
        }
        
        return score, details
        
    except Exception as e:
        print(f"Error fetching VIX: {e}")
        return None, None


def get_sp500_momentum_score() -> Tuple[Optional[float], Optional[Dict]]:
    """
    Get S&P 500 momentum score based on RECENT PRICE ACTION + 52-week position.
    Heavily weights today's price change to reflect current sentiment.
    
    Formula: 60% today's change + 40% position in 52W range
    This ensures selldowns are immediately reflected in fear score.
    
    Returns: (score, details_dict)
    """
    try:
        url = f'https://financialmodelingprep.com/api/v3/quote/^GSPC?apikey={FMP_API_KEY}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"S&P 500 fetch failed: {response.status_code}")
            return None, None
            
        data = response.json()
        if not data:
            return None, None
            
        current_price = data[0].get('price', 0)
        year_high = data[0].get('yearHigh', 0)
        year_low = data[0].get('yearLow', 0)
        change_pct = data[0].get('changesPercentage', 0)
        
        if year_high == year_low:
            return 50, None  # Edge case, return neutral
            
        # Calculate position in 52-week range (0-100)
        position = ((current_price - year_low) / (year_high - year_low)) * 100
        
        # Convert today's price change to score (0-100)
        # -2% or worse = 0, +2% or better = 100
        change_score = 50 + (change_pct / 2) * 50  # Map -2% to +2% onto 0-100
        change_score = max(0, min(100, change_score))  # Clamp
        
        # Weighted score: 60% today's action, 40% historical position
        # This makes it responsive to current market moves
        score = (change_score * 0.6) + (position * 0.4)
        
        if score >= 75:
            interpretation = "Strong Momentum (Greed)"
        elif score >= 60:
            interpretation = "Positive Momentum"
        elif score >= 40:
            interpretation = "Neutral"
        elif score >= 25:
            interpretation = "Negative Momentum"
        else:
            interpretation = "Weak Momentum (Fear)"
            
        details = {
            'price': current_price,
            'year_high': year_high,
            'year_low': year_low,
            'position_pct': round(position, 1),
            'change_pct': change_pct,
            'interpretation': interpretation,
            'component': 'S&P 500 Momentum'
        }
        
        return score, details
        
    except Exception as e:
        print(f"Error fetching S&P 500: {e}")
        return None, None


def get_treasury_yield_score() -> Tuple[Optional[float], Optional[Dict]]:
    """
    Get treasury yield score based on 10Y yield level and recent change.
    Rising yields (safe haven demand dropping) = Greed
    Falling yields (flight to safety) = Fear
    
    Uses both absolute level and 20-day change.
    
    Returns: (score, details_dict)
    """
    try:
        # Get current 10Y yield
        url = f'https://financialmodelingprep.com/api/v3/quote/^TNX?apikey={FMP_API_KEY}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Treasury yield fetch failed: {response.status_code}")
            return None, None
            
        data = response.json()
        if not data:
            return None, None
            
        current_yield = data[0].get('price', 0)
        change_pct = data[0].get('changesPercentage', 0)
        
        # Score based on recent change direction
        # Positive change (rising yields) = less fear = higher score
        # Negative change (falling yields) = more fear = lower score
        if change_pct > 2:
            score = 80
            interpretation = "Greed (Yields Rising)"
        elif change_pct > 0:
            score = 50 + (change_pct / 2) * 30  # 50-80
            interpretation = "Slight Greed"
        elif change_pct > -2:
            score = 50 + (change_pct / 2) * 30  # 20-50
            interpretation = "Slight Fear"
        else:
            score = 20
            interpretation = "Fear (Yields Falling)"
            
        details = {
            'yield': current_yield,
            'change_pct': change_pct,
            'interpretation': interpretation,
            'component': '10Y Treasury'
        }
        
        return score, details
        
    except Exception as e:
        print(f"Error fetching treasury yields: {e}")
        return None, None


def get_market_breadth_score() -> Tuple[Optional[float], Optional[Dict]]:
    """
    Get market breadth score by comparing major indices performance.
    All indices up strongly = Greed
    All indices down = Fear
    
    Uses Dow, S&P, Nasdaq to gauge broad market participation.
    
    Returns: (score, details_dict)
    """
    try:
        # Get multiple major indices
        symbols = ['^DJI', '^GSPC', '^IXIC']  # Dow, S&P 500, Nasdaq
        url = f'https://financialmodelingprep.com/api/v3/quote/{",".join(symbols)}?apikey={FMP_API_KEY}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Market breadth fetch failed: {response.status_code}")
            return None, None
            
        data = response.json()
        if not data or len(data) < 3:
            return None, None
            
        changes = [d.get('changesPercentage', 0) for d in data]
        avg_change = sum(changes) / len(changes)
        
        # Count positive vs negative indices
        positive_count = sum(1 for c in changes if c > 0)
        
        # Score based on average change and breadth
        if avg_change > 1 and positive_count >= 2:
            score = 80
            interpretation = "Strong Breadth (Greed)"
        elif avg_change > 0:
            score = 50 + (avg_change * 15)  # Scale to 50-80
            interpretation = "Positive Breadth"
        elif avg_change > -1:
            score = 50 + (avg_change * 15)  # Scale to 20-50
            interpretation = "Negative Breadth"
        else:
            score = 20
            interpretation = "Weak Breadth (Fear)"
            
        score = max(0, min(100, score))  # Clamp to 0-100
            
        details = {
            'dow_change': changes[0] if len(changes) > 0 else 0,
            'sp500_change': changes[1] if len(changes) > 1 else 0,
            'nasdaq_change': changes[2] if len(changes) > 2 else 0,
            'avg_change': round(avg_change, 2),
            'positive_count': positive_count,
            'interpretation': interpretation,
            'component': 'Market Breadth'
        }
        
        return score, details
        
    except Exception as e:
        print(f"Error fetching market breadth: {e}")
        return None, None


def calculate_market_sentiment() -> Dict:
    """
    Calculate comprehensive market sentiment score (0-100).
    
    Components (each 25%):
    - VIX Level (fear gauge)
    - S&P 500 Momentum (market position)
    - Treasury Yields (safe haven demand)
    - Market Breadth (participation)
    
    Returns dict with:
    - overall_score: 0-100 (0=Extreme Fear, 100=Extreme Greed)
    - interpretation: Text description
    - components: Dict of individual component scores and details
    - timestamp: When calculated
    """
    print("Calculating market sentiment...")
    
    components = {}
    scores = []
    weights = []
    
    # VIX (25% weight)
    vix_score, vix_details = get_vix_score()
    if vix_score is not None:
        components['vix'] = vix_details
        scores.append(vix_score)
        weights.append(0.25)
    
    # S&P 500 Momentum (25% weight)
    sp500_score, sp500_details = get_sp500_momentum_score()
    if sp500_score is not None:
        components['sp500_momentum'] = sp500_details
        scores.append(sp500_score)
        weights.append(0.25)
    
    # Treasury Yields (25% weight)
    treasury_score, treasury_details = get_treasury_yield_score()
    if treasury_score is not None:
        components['treasury_yields'] = treasury_details
        scores.append(treasury_score)
        weights.append(0.25)
    
    # Market Breadth (25% weight)
    breadth_score, breadth_details = get_market_breadth_score()
    if breadth_score is not None:
        components['market_breadth'] = breadth_details
        scores.append(breadth_score)
        weights.append(0.25)
    
    # Calculate weighted average
    if not scores:
        return {
            'error': 'Unable to calculate sentiment - no data available',
            'timestamp': datetime.now().isoformat()
        }
    
    # Normalize weights if some components failed
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    
    overall_score = sum(s * w for s, w in zip(scores, normalized_weights))
    
    # Interpret overall score
    if overall_score >= 75:
        interpretation = "Extreme Greed"
        emoji = "🚀"
    elif overall_score >= 60:
        interpretation = "Greed"
        emoji = "📈"
    elif overall_score >= 40:
        interpretation = "Neutral"
        emoji = "😐"
    elif overall_score >= 25:
        interpretation = "Fear"
        emoji = "📉"
    else:
        interpretation = "Extreme Fear"
        emoji = "😱"
    
    result = {
        'overall_score': round(overall_score, 1),
        'interpretation': interpretation,
        'emoji': emoji,
        'components': components,
        'component_count': len(components),
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"Market Sentiment: {overall_score:.1f} ({interpretation})")
    return result


def format_sentiment_message(sentiment: Dict) -> str:
    """
    Format sentiment data for Telegram message.
    
    Args:
        sentiment: Dict from calculate_market_sentiment()
        
    Returns:
        Formatted message string
    """
    if 'error' in sentiment:
        return f"❌ {sentiment['error']}"
    
    score = sentiment['overall_score']
    interpretation = sentiment['interpretation']
    emoji = sentiment['emoji']
    components = sentiment['components']
    
    msg = f"{emoji} **Market Sentiment Index: {score}/100**\n"
    msg += f"**Status: {interpretation}**\n\n"
    
    msg += "📊 **Component Breakdown:**\n"
    
    # VIX
    if 'vix' in components:
        vix = components['vix']
        msg += f"\n🔥 **VIX (Volatility):** {vix['value']:.2f} ({vix['change_pct']:+.2f}%)\n"
        msg += f"   └ {vix['interpretation']}\n"
    
    # S&P 500 Momentum
    if 'sp500_momentum' in components:
        sp = components['sp500_momentum']
        msg += f"\n📈 **S&P 500 Position:** ${sp['price']:.2f} ({sp['change_pct']:+.2f}%)\n"
        msg += f"   └ {sp['position_pct']:.1f}% from 52W low to high\n"
        msg += f"   └ {sp['interpretation']}\n"
    
    # Treasury Yields
    if 'treasury_yields' in components:
        tn = components['treasury_yields']
        msg += f"\n💰 **10Y Treasury:** {tn['yield']:.3f}% ({tn['change_pct']:+.2f}%)\n"
        msg += f"   └ {tn['interpretation']}\n"
    
    # Market Breadth
    if 'market_breadth' in components:
        mb = components['market_breadth']
        msg += f"\n🌐 **Market Breadth:** {mb['positive_count']}/3 indices positive\n"
        msg += f"   └ Avg change: {mb['avg_change']:+.2f}%\n"
        msg += f"   └ {mb['interpretation']}\n"
    
    msg += f"\n⏰ Updated: {datetime.fromisoformat(sentiment['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}"
    
    return msg
