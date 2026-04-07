# engine.py

import streamlit as st   # 🔥 FIX: ensure this is first
import os
from pathlib import Path
from google import genai # type: ignore
from google.genai import types # type: ignore@st.cache_resource
def initialize_client():
    """Initializes the Gemini client securely using Streamlit Secrets or ENV fallback."""

    # ================== 🔥 UPDATED ==================
    api_key = None

    # 1. Try Streamlit secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    # 2. Fallback to environment variable (IMPORTANT FIX)
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    # 3. Final check
    if not api_key:
        return None, (
            "🛑 GEMINI_API_KEY not found.\n\n"
            "Fix:\n"
            "1. Add it in Streamlit Cloud Secrets OR\n"
            "2. Set environment variable GEMINI_API_KEY"
        )

    # 4. Initialize client
    try:
        client = genai.Client(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"Error initializing Gemini Client: {e}"
    # ===============================================