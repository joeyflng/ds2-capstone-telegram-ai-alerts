"""
Yahoo Finance API Rate Limiting Configuration

This file contains settings to prevent hitting rate limits when accessing Yahoo Finance.
Adjust these settings based on your usage patterns and observed rate limiting behavior.
"""

# ===== RATE LIMITING SETTINGS =====

# Basic rate limiting
RATE_LIMIT_DELAY = 3.0  # Seconds to wait between requests
MAX_RETRIES = 4  # Maximum retry attempts for failed requests
REQUEST_TIMEOUT = 15  # Request timeout in seconds

# Caching settings
CACHE_DURATION_QUOTES = 60  # Cache quotes for 1 minute
CACHE_DURATION_HISTORY = 300  # Cache historical data for 5 minutes

# Backoff settings
BASE_BACKOFF_DELAY = 2  # Base delay for exponential backoff
MAX_BACKOFF_DELAY = 30  # Maximum backoff delay
JITTER_RANGE = (0.5, 1.5)  # Random jitter range to avoid synchronized requests

# ===== USAGE TIPS =====
"""
Rate Limiting Best Practices:

1. INCREASE DELAYS if you're getting frequent 429 errors:
   - Set RATE_LIMIT_DELAY to 5.0 or higher
   - Increase MAX_RETRIES to 5-6

2. REDUCE CACHE DURATION for more real-time data:
   - Set CACHE_DURATION_QUOTES to 30 seconds
   - Keep CACHE_DURATION_HISTORY at 300 seconds

3. FOR HIGH-FREQUENCY USAGE:
   - Consider implementing request queuing
   - Use multiple API keys if available
   - Implement IP rotation for production

4. MONITOR YOUR USAGE:
   - Yahoo Finance allows ~2000 requests/hour per IP
   - Peak hours (9:30-4:00 ET) have stricter limits
   - After-hours and weekends are more lenient

5. ERROR HANDLING:
   - 429 = Rate limited (retry with backoff)
   - 403 = Forbidden (check user agent/headers)
   - 404 = Symbol not found (don't retry)
   - 500 = Server error (retry with caution)
"""

# ===== ADVANCED SETTINGS =====

# User agent rotation (helps avoid detection)
USE_USER_AGENT_ROTATION = True

# Session management (keeps connections alive)
USE_SESSION_POOLING = True

# Request headers optimization
CUSTOM_HEADERS = {
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Referer': 'https://finance.yahoo.com/',
    'X-Requested-With': 'XMLHttpRequest'
}

# Alternative endpoints (if main endpoint is heavily rate limited)
YAHOO_ENDPOINTS = {
    'primary': 'https://query1.finance.yahoo.com/v8/finance/chart/',
    'secondary': 'https://query2.finance.yahoo.com/v8/finance/chart/',
    'fallback': 'https://finance.yahoo.com/quote/{}/history'
}

# Emergency fallback settings
FALLBACK_TO_MOCK_AFTER_RETRIES = True
MOCK_DATA_WARNING = True