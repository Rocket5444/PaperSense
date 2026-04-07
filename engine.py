# engine.py

import streamlit as st
import os
from pathlib import Path
from google import genai
from google.genai import types

# ================== 🔥 FIXED CLIENT INIT ==================
def initialize_client():
    """Initialize Gemini client (Cloud + Local safe)"""

    api_key = None

    # Try Streamlit secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    # Fallback to environment variable
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None, "❌ GEMINI_API_KEY not found."

    try:
        client = genai.Client(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"Client init error: {e}"


# ================== FILE UPLOAD ==================
def upload_document(client: genai.Client, uploaded_file_obj) -> types.File:
    file_name = uploaded_file_obj.name
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)

    temp_path = temp_dir / file_name

    with open(temp_path, "wb") as f:
        f.write(uploaded_file_obj.getbuffer())

    try:
        uploaded_file = client.files.upload(file=str(temp_path))
        return uploaded_file
    except Exception as e:
        st.error(f"Upload error: {e}")
        return None
    finally:
        os.remove(temp_path)
        if not os.listdir(temp_dir):
            os.rmdir(temp_dir)


# ================== PROCESS ==================
def process_document(client: genai.Client, uploaded_file: types.File, prompt: str):
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt],
        )
        return response.text
    except Exception as e:
        return f"❌ Processing error: {e}"


# ================== DELETE ==================
def delete_uploaded_file(client: genai.Client, uploaded_file: types.File):
    try:
        client.files.delete(name=uploaded_file.name)
        st.toast("File deleted successfully")
    except Exception as e:
        st.warning(f"Delete failed: {e}")