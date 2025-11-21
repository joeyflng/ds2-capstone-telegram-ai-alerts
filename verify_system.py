#!/usr/bin/env python3
"""
System Verification Script
Tests the clean modular architecture and all dependencies
"""

import sys
import os
import importlib.util

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_dependencies():
    """Test all required dependencies"""
    print("🔍 Testing Dependencies...")
    
    dependencies = [
        'pandas', 'numpy', 'requests', 'yfinance', 
        'matplotlib', 'groq', 'schedule', 'dotenv'
    ]
    
    for dep in dependencies:
        try:
            if dep == 'dotenv':
                from dotenv import load_dotenv
            else:
                __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} - MISSING")
            return False
    
    return True

def test_modules():
    """Test all application modules"""
    print("\n🏗️ Testing Modular Architecture...")
    
    modules = [
        ('config', 'Configuration'),
        ('core.telegram_client', 'Telegram Client'),
        ('core.interactive_bot', 'Interactive Bot'),
        ('services.ai_research', 'AI Research'),
        ('services.data_providers', 'Data Providers'),
        ('services.earnings', 'Earnings Service'),
        ('analytics.alerts', 'Alert System'),
        ('analytics.charts', 'Chart Generation'),
        ('utils.logs', 'Logging Utils'),
        ('utils.persistence', 'Persistence Utils')
    ]
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✅ {description} ({module_name})")
        except ImportError as e:
            print(f"  ❌ {description} ({module_name}) - {e}")
            return False
    
    return True

def test_bots():
    """Test bot initialization"""
    print("\n🤖 Testing Bot Initialization...")
    
    try:
        from bot_modular import TelegramStockBot
        bot = TelegramStockBot()
        print("  ✅ Alert Bot (bot_modular.TelegramStockBot)")
    except Exception as e:
        print(f"  ❌ Alert Bot - {e}")
        return False
    
    try:
        from core.interactive_bot import InteractiveTelegramBot
        interactive_bot = InteractiveTelegramBot()
        print(f"  ✅ Interactive Bot (Commands: {len(interactive_bot.commands)})")
    except Exception as e:
        print(f"  ❌ Interactive Bot - {e}")
        return False
    
    return True

def check_file_structure():
    """Verify clean file structure"""
    print("\n📁 Checking File Structure...")
    
    required_files = [
        'app/bot_modular.py',
        'app/config.py',
        'app/core/telegram_client.py',
        'app/core/interactive_bot.py',
        'app/services/ai_research.py',
        'app/services/data_providers.py',
        'app/services/earnings.py',
        'app/analytics/alerts.py',
        'app/analytics/charts.py',
        'app/utils/logs.py',
        'app/utils/persistence.py',
        'bot_interactive.py',
        'requirements.txt',
        'environment.yml'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def main():
    """Run all verification tests"""
    print("🚀 System Verification for Clean Modular Architecture")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Modules", test_modules),
        ("Bots", test_bots),
        ("File Structure", check_file_structure)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! System is ready for deployment.")
        print("\n🚀 To start the bot:")
        print("   python bot_interactive.py")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())