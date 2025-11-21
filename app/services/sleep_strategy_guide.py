"""
Yahoo Finance API Rate Limiting Strategy Guide

Based on testing and optimization, here are the best practices for sleeping between stock requests:
"""

# ===== SLEEP STRATEGY RECOMMENDATIONS =====

# 1. SINGLE STOCK REQUESTS (Interactive use)
SINGLE_REQUEST_SLEEP = 0  # No sleep needed, built-in rate limiting handles it

# 2. SMALL BATCHES (2-3 stocks)
SMALL_BATCH_SLEEP = 2.0   # 2 seconds between stocks
SMALL_BATCH_SIZE = 3

# 3. MEDIUM BATCHES (4-10 stocks)  
MEDIUM_BATCH_SLEEP = 2.0  # 2 seconds between stocks
MEDIUM_BATCH_COOLDOWN = 10.0  # 10 seconds between groups of 3
MEDIUM_BATCH_SIZE = 3

# 4. LARGE BATCHES (10+ stocks)
LARGE_BATCH_SLEEP = 3.0   # 3 seconds between stocks
LARGE_BATCH_COOLDOWN = 15.0  # 15 seconds between groups of 3
LARGE_BATCH_SIZE = 3

# 5. HIGH-FREQUENCY SCENARIOS (alerts, monitoring)
HF_SLEEP = 5.0  # 5 seconds between requests
HF_MAX_REQUESTS_PER_MINUTE = 10

# ===== WHEN TO USE SLEEP =====

"""
✅ DEFINITELY USE SLEEP WHEN:
- Processing multiple stocks in sequence (>2 stocks)
- Running automated alerts/monitoring  
- During market hours (9:30 AM - 4:00 PM ET)
- After hitting rate limits (429 errors)
- Processing historical data for multiple stocks

❌ SKIP SLEEP WHEN:
- Single stock lookup (interactive use)
- Data is already cached (< 1 minute old)
- After-hours/weekend requests (less strict limits)
- Using different endpoints/APIs

⚡ SMART SLEEP STRATEGIES:
1. Progressive delays: Start with 1s, increase to 3s after rate limits
2. Jittered delays: Add random 0.5-1.5s to avoid synchronized requests  
3. Exponential backoff: Double delay after each 429 error
4. Batch processing: Group requests with longer cooldowns
5. Cache utilization: Check cache before making requests
"""

# ===== IMPLEMENTATION EXAMPLES =====

# Example 1: Simple batch with sleep
def process_stocks_simple(symbols):
    results = []
    for i, symbol in enumerate(symbols):
        result = get_quote(symbol)
        results.append(result)
        
        # Sleep between stocks (except last one)
        if i < len(symbols) - 1:
            time.sleep(2.0)  # ✅ 2 second delay
    
    return results

# Example 2: Smart batch with progressive delays
def process_stocks_smart(symbols):
    results = []
    base_delay = 2.0
    
    for i, symbol in enumerate(symbols):
        # Increase delay if we're hitting rate limits
        if i > 0 and previous_request_failed:
            base_delay = min(base_delay * 1.5, 5.0)  # Cap at 5s
        
        result = get_quote(symbol)
        results.append(result)
        
        if i < len(symbols) - 1:
            jittered_delay = base_delay * random.uniform(0.8, 1.2)
            time.sleep(jittered_delay)  # ✅ Smart jittered delay
    
    return results

# Example 3: Batch processing with cooldowns
def process_stocks_batched(symbols, batch_size=3):
    results = []
    
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        
        # Process batch with inter-stock delays
        for j, symbol in enumerate(batch):
            result = get_quote(symbol)
            results.append(result)
            
            if j < len(batch) - 1:
                time.sleep(2.0)  # ✅ Inter-stock delay
        
        # Cooldown between batches
        if i + batch_size < len(symbols):
            time.sleep(10.0)  # ✅ Batch cooldown
    
    return results

# ===== RATE LIMITING INDICATORS =====

"""
🚨 INCREASE SLEEP WHEN YOU SEE:
- Multiple 429 errors in sequence
- Requests taking >15 seconds due to retries  
- Success rate dropping below 80%
- Consistent rate limiting across different stocks

⚡ DECREASE SLEEP WHEN YOU SEE:
- All requests succeeding quickly (< 3 seconds)
- No 429 errors for 10+ consecutive requests
- Cache hit rates > 50%
- Off-peak hours usage

📊 MONITORING METRICS:
- Request success rate (target: >90%)
- Average request time (target: <5 seconds)
- Cache hit rate (target: >30%)
- Rate limit encounters per hour (target: <5)
"""

# ===== FINAL RECOMMENDATIONS =====

"""
🎯 OPTIMAL SLEEP SETTINGS FOR DIFFERENT SCENARIOS:

📱 BOT COMMANDS (Interactive):
- Single stock: No sleep (cache + built-in delays)
- Multiple stocks: 2s between stocks

📊 WEB APP (User browsing):
- Portfolio view: 2s between stocks, batch size 3
- Comparison: 3s between stocks

🤖 ALERTS (Automated):
- Monitoring loop: 5s between stocks
- Batch alerts: 3s between stocks, 15s batch cooldown  

📈 ANALYTICS (Bulk processing):
- Historical data: 3-5s between stocks
- Large datasets: Use smart batching with 10-15s cooldowns

⏰ TIME-BASED ADJUSTMENTS:
- Market hours (9:30-4 ET): +50% longer delays
- Pre/post market: Normal delays
- Weekends: -25% shorter delays (if API allows)
"""