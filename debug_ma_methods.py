#!/usr/bin/env python3
"""Debug script to compare data retrieval methods for MA crossover detection"""

import sys
import os
sys.path.append('/home/joey/projects/capstone/capstone-telegram-ai-alerts/app')

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def test_data_methods(symbol="AAPL"):
    """Compare the two data retrieval methods"""
    print(f"🔍 Testing data retrieval methods for {symbol}")
    print("="*80)
    
    # Method 1: Manual test method (yf.download with 250 days)
    print("📊 Method 1: yf.download() with 250 days (manual test)")
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=250)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        hist1 = yf.download(symbol, start=start_date_str, end=end_date_str, progress=False)
        if len(hist1) > 0:
            if isinstance(hist1.columns, pd.MultiIndex):
                prices1 = hist1[('Close', symbol)].tolist()
            else:
                prices1 = hist1['Close'].tolist()
            dates1 = [date.strftime('%Y-%m-%d') for date in hist1.index]
            print(f"  ✅ Retrieved {len(prices1)} data points")
            print(f"  📅 Date range: {dates1[0]} to {dates1[-1]}")
            print(f"  💰 Latest price: ${prices1[-1]:.2f}")
        else:
            print("  ❌ No data retrieved")
            prices1, dates1 = [], []
    except Exception as e:
        print(f"  ❌ Error: {e}")
        prices1, dates1 = [], []
    
    print()
    
    # Method 2: Automated method (ticker.history with 5y period)
    print("📊 Method 2: ticker.history() with 5y period (automated)")
    try:
        ticker = yf.Ticker(symbol)
        hist2 = ticker.history(period="5y")
        if len(hist2) > 0:
            prices2 = hist2['Close'].tolist()
            dates2 = [date.strftime('%Y-%m-%d') for date in hist2.index]
            print(f"  ✅ Retrieved {len(prices2)} data points")
            print(f"  📅 Date range: {dates2[0]} to {dates2[-1]}")
            print(f"  💰 Latest price: ${prices2[-1]:.2f}")
        else:
            print("  ❌ No data retrieved")
            prices2, dates2 = [], []
    except Exception as e:
        print(f"  ❌ Error: {e}")
        prices2, dates2 = [], []
    
    print()
    
    # Compare results
    print("🔄 Comparison:")
    if prices1 and prices2:
        print(f"  📊 Data points: Method 1: {len(prices1)}, Method 2: {len(prices2)}")
        print(f"  💰 Latest price match: {abs(prices1[-1] - prices2[-1]) < 0.01}")
        
        # Check if we have enough data for 200-day MA
        print(f"  📈 Sufficient for 200-day MA: Method 1: {len(prices1) >= 200}, Method 2: {len(prices2) >= 200}")
        
        # Calculate simple 50 and 200 day MAs for comparison
        if len(prices1) >= 200:
            ma50_1 = sum(prices1[-50:]) / 50
            ma200_1 = sum(prices1[-200:]) / 200
            print(f"  📈 Method 1 MAs: 50-day: ${ma50_1:.2f}, 200-day: ${ma200_1:.2f}")
            print(f"  📊 Method 1 Position: {'50 > 200' if ma50_1 > ma200_1 else '50 < 200'}")
        
        if len(prices2) >= 200:
            ma50_2 = sum(prices2[-50:]) / 50
            ma200_2 = sum(prices2[-200:]) / 200
            print(f"  📈 Method 2 MAs: 50-day: ${ma50_2:.2f}, 200-day: ${ma200_2:.2f}")
            print(f"  📊 Method 2 Position: {'50 > 200' if ma50_2 > ma200_2 else '50 < 200'}")
    
    return prices1, dates1, prices2, dates2

if __name__ == "__main__":
    # Test with AAPL first
    print("🧪 MA Crossover Data Method Comparison")
    print("="*80)
    test_data_methods("AAPL")
    
    print("\n" + "="*80)
    
    # Test with a few other symbols
    for symbol in ["MSFT", "GOOGL"]:
        print(f"\n🔍 Quick test for {symbol}:")
        try:
            # Quick test with both methods
            ticker = yf.Ticker(symbol)
            hist_5y = ticker.history(period="5y")
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=250)
            hist_250d = yf.download(symbol, start=start_date.strftime('%Y-%m-%d'), 
                                  end=end_date.strftime('%Y-%m-%d'), progress=False)
            
            print(f"  📊 5y data: {len(hist_5y)} points, 250d data: {len(hist_250d)} points")
            
            if len(hist_5y) >= 200:
                prices_5y = hist_5y['Close'].tolist()
                ma50_5y = sum(prices_5y[-50:]) / 50
                ma200_5y = sum(prices_5y[-200:]) / 200
                trend_5y = "Bullish" if ma50_5y > ma200_5y else "Bearish"
                print(f"  📈 5y method: {trend_5y} (50MA: ${ma50_5y:.2f}, 200MA: ${ma200_5y:.2f})")
            
            if len(hist_250d) >= 200:
                if isinstance(hist_250d.columns, pd.MultiIndex):
                    prices_250d = hist_250d[('Close', symbol)].tolist()
                else:
                    prices_250d = hist_250d['Close'].tolist()
                ma50_250d = sum(prices_250d[-50:]) / 50
                ma200_250d = sum(prices_250d[-200:]) / 200
                trend_250d = "Bullish" if ma50_250d > ma200_250d else "Bearish"
                print(f"  📈 250d method: {trend_250d} (50MA: ${ma50_250d:.2f}, 200MA: ${ma200_250d:.2f})")
                
        except Exception as e:
            print(f"  ❌ Error testing {symbol}: {e}")