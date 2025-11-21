#!/usr/bin/env python3
"""
Setup script for Telegram Stock Alert Bot
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install required dependencies"""
    print("🚀 Installing Telegram Stock Alert Bot dependencies...")
    
    # Check Python version
    check_python_version()
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        return False
    
    return True

def setup_environment():
    """Set up environment file if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📋 Creating .env file from template...")
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ Created .env file - please configure your API keys!")
        print("📝 Edit .env with your:")
        print("   - TELEGRAM_BOT_TOKEN (from @BotFather)")
        print("   - TELEGRAM_CHAT_ID (your Telegram user ID)")  
        print("   - FMP_API_KEY (from financialmodelingprep.com)")
        print("   - GROQ_API_KEY (from console.groq.com)")
    else:
        print("✅ .env file already exists")

def create_data_directories():
    """Create necessary data directories"""
    directories = [
        "app/data",
        "app/data/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def test_installation():
    """Test basic functionality"""
    print("\n🧪 Testing installation...")
    
    # Test basic imports
    test_commands = [
        ("python -c 'import pandas; print(f\"✅ pandas {pandas.__version__}\")'", "Testing pandas"),
        ("python -c 'import yfinance; print(f\"✅ yfinance {yfinance.__version__}\")'", "Testing yfinance"),
        ("python -c 'import matplotlib; print(f\"✅ matplotlib {matplotlib.__version__}\")'", "Testing matplotlib"),
        ("python -c 'from groq import Groq; print(\"✅ groq available\")'", "Testing groq"),
        ("python app/config.py", "Testing configuration")
    ]
    
    all_tests_passed = True
    for command, description in test_commands:
        if not run_command(command, description):
            all_tests_passed = False
    
    if all_tests_passed:
        print("\n🎉 Installation completed successfully!")
        print("\n📖 Next steps:")
        print("1. Configure your API keys in .env file")  
        print("2. Test basic functionality: python app/test_bot.py test")
        print("3. Test LLM integration: python app/test_bot.py testllm") 
        print("4. Run company research: python app/test_bot.py research AAPL")
        print("5. Start the bot: python app/test_bot.py run")
    else:
        print("\n⚠️  Some tests failed. Check error messages above.")

if __name__ == "__main__":
    print("🤖 Telegram Stock Alert Bot Setup")
    print("=" * 50)
    
    # Install dependencies
    if install_dependencies():
        # Setup environment
        setup_environment()
        
        # Create directories
        create_data_directories()
        
        # Test installation
        test_installation()
    else:
        print("❌ Installation failed. Please check error messages above.")
        sys.exit(1)