import streamlit as st
import os
from pathlib import Path
import pandas as pd
from google import genai
from google.genai import types

# ================== CLIENT INIT ==================
def initialize_client():
    try:
        api_key = st.secrets['GEMINI_API_KEY']
        client = genai.Client(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f'Client init error: {e}'

# ================== HELPERS ==================
def is_spreadsheet(filename:str):
    ext = Path(filename).suffix.lower()
    return ext in ['.xlsx','.xls','.csv','.tsv']


def spreadsheet_to_text(uploaded_file_obj):
    name = uploaded_file_obj.name.lower()
    if name.endswith('.csv'):
        df = pd.read_csv(uploaded_file_obj)
        return df.to_markdown(index=False)
    if name.endswith('.tsv'):
        df = pd.read_csv(uploaded_file_obj, sep='\t')
        return df.to_markdown(index=False)
    # excel
    sheets = pd.read_excel(uploaded_file_obj, sheet_name=None)
    parts = []
    for sheet, df in sheets.items():
        parts.append(f'## Sheet: {sheet}')
        parts.append(df.fillna('').to_markdown(index=False))
    return '\n\n'.join(parts)

# ================== FILE UPLOAD ==================
def upload_document(client: genai.Client, uploaded_file_obj):
    # For spreadsheets, do NOT upload to Gemini File API
    if is_spreadsheet(uploaded_file_obj.name):
        text = spreadsheet_to_text(uploaded_file_obj)
        return {'kind':'spreadsheet_text','content':text,'name':uploaded_file_obj.name}

    file_name = uploaded_file_obj.name
    temp_dir = Path('temp_uploads')
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file_name

    with open(temp_path, 'wb') as f:
        f.write(uploaded_file_obj.getbuffer())

    try:
        uploaded_file = client.files.upload(file=str(temp_path))
        return {'kind':'gemini_file','content':uploaded_file,'name':file_name}
    finally:
        if temp_path.exists():
            os.remove(temp_path)
        if temp_dir.exists() and not os.listdir(temp_dir):
            os.rmdir(temp_dir)

# ================== PROCESS ==================
def process_document(client: genai.Client, uploaded_doc, prompt: str):
    try:
        if uploaded_doc['kind'] == 'spreadsheet_text':
            contents = [f"Spreadsheet data from {uploaded_doc['name']}:\n\n{uploaded_doc['content']}", prompt]
        else:
            contents = [uploaded_doc['content'], prompt]

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
        )
        return response.text
    except Exception as e:
        return f'❌ Processing error: {e}'

# ================== DELETE ==================
def delete_uploaded_file(client: genai.Client, uploaded_doc):
    try:
        if uploaded_doc['kind'] == 'gemini_file':
            client.files.delete(name=uploaded_doc['content'].name)
        st.toast('File cleared successfully')
    except Exception as e:
        st.warning(f'Delete failed: {e}')
