import os
import streamlit as st

def get_env_variable(key: str, default: str = "") -> str:
    """
    Get environment variable with Hugging Face Spaces support.
    Checks both st.secrets (HF Spaces) and os.environ (local).
    """
    # Try Hugging Face Spaces secrets first
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    # Fallback to environment variables (local development)
    return os.getenv(key, default)

# Configuration
GROQ_API_KEY = get_env_variable("GROQ_API_KEY", "")
FMP_API_KEY = get_env_variable("FMP_API_KEY", "")
FMP_DELAY_SECONDS = 3  # Rate limiting for FMP API
