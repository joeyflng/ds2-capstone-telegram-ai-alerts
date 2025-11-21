#!/usr/bin/env python3
"""
Verify Hugging Face Spaces deployment readiness
Checks all required files and configurations
"""
import os
import sys

def check_file(filepath, description):
    """Check if file exists"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists

def check_file_content(filepath, required_strings, description):
    """Check if file contains required content"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: File not found")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    missing = [s for s in required_strings if s not in content]
    if missing:
        print(f"❌ {description}: Missing required content: {missing}")
        return False
    
    print(f"✅ {description}: All required content present")
    return True

def main():
    print("=" * 60)
    print("🚀 Hugging Face Spaces Deployment Readiness Check")
    print("=" * 60)
    print()
    
    base_path = "market-chat-web"
    all_checks_passed = True
    
    # Check required files
    print("📁 Checking Required Files:")
    all_checks_passed &= check_file(f"{base_path}/app.py", "Main application")
    all_checks_passed &= check_file(f"{base_path}/requirements.txt", "Dependencies")
    all_checks_passed &= check_file(f"{base_path}/README.md", "Space README")
    all_checks_passed &= check_file(f"{base_path}/.gitignore", "Git ignore file")
    all_checks_passed &= check_file(f"{base_path}/utils/market.py", "Market utilities")
    all_checks_passed &= check_file(f"{base_path}/utils/llm.py", "LLM utilities")
    print()
    
    # Check app.py configuration
    print("⚙️  Checking App Configuration:")
    all_checks_passed &= check_file_content(
        f"{base_path}/app.py",
        ["import streamlit as st", "from utils.market import", "from utils.llm import"],
        "App imports"
    )
    print()
    
    # Check requirements.txt
    print("📦 Checking Dependencies:")
    all_checks_passed &= check_file_content(
        f"{base_path}/requirements.txt",
        ["streamlit", "pandas", "plotly", "yfinance", "groq"],
        "Required packages"
    )
    print()
    
    # Check LLM configuration for HF Spaces support
    print("🔑 Checking HF Spaces Secrets Support:")
    all_checks_passed &= check_file_content(
        f"{base_path}/utils/llm.py",
        ["st.secrets", "get_api_key", "GROQ_API_KEY"],
        "Secrets configuration"
    )
    print()
    
    # Check README.md has deployment info
    print("📝 Checking Documentation:")
    all_checks_passed &= check_file_content(
        f"{base_path}/README.md",
        ["sdk: streamlit", "GROQ_API_KEY", "Repository Secrets"],
        "Deployment instructions"
    )
    print()
    
    # Summary
    print("=" * 60)
    if all_checks_passed:
        print("✅ All checks passed! Ready for Hugging Face Spaces deployment")
        print()
        print("Next steps:")
        print("1. Create new Space at https://huggingface.co/spaces")
        print("2. Select 'Streamlit' as SDK")
        print("3. Clone Space and copy market-chat-web/* files")
        print("4. Push to HF: git add . && git commit -m 'Deploy' && git push")
        print("5. Add GROQ_API_KEY to Repository Secrets")
        print()
        print("See DEPLOYMENT.md for detailed instructions")
        return 0
    else:
        print("❌ Some checks failed. Please fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
