# app.py

import streamlit as st
from engine import (
    initialize_client, 
    upload_document, 
    process_document, 
    delete_uploaded_file
)

# ================== 🔐 NEW: AUTH SYSTEM ==================
def authenticate_user():
    """Simple token-based authentication"""
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Secure Access Required")

        token_input = st.text_input("Enter Access Token", type="password")

        if st.button("Login"):
            try:
                correct_token = st.secrets["APP_AUTH_TOKEN"]
            except KeyError:
                st.error("Auth token not set in secrets.")
                st.stop()

            if token_input == correct_token:
                st.session_state.authenticated = True
                st.success("✅ Access Granted")
                st.rerun()
            else:
                st.error("❌ Invalid Token")

        st.stop()
# ========================================================


# --- CHAT FUNCTIONALITY ---
def chat_with_document(client):
    
    if 'uploaded_file_object' not in st.session_state or st.session_state.uploaded_file_object is None:
        st.info("Upload a document in the sidebar to begin chatting.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append(
            {"role": "assistant", "content": "Document analysis ready! Ask me any question about the content."}
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about the document..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing content..."):
                file_obj = st.session_state.uploaded_file_object
                
                response = process_document(client, file_obj, prompt)
                
                st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


# --- MAIN UI ---
def main():
    # 🔐 NEW: AUTH CHECK
    authenticate_user()

    st.set_page_config(page_title="Gemini Document Analyzer", layout="wide")
    st.title("📄 AI Document Analyzer & Chat")
    st.markdown("Upload any document (PDF, TXT, DOCX, etc.) and chat with it.")
    st.divider()

    client, error_message = initialize_client()
    
    if client is None:
        st.error("🛑 Client failed to initialize. " + error_message)
        return 

    if 'uploaded_file_object' not in st.session_state:
        st.session_state.uploaded_file_object = None
    if 'cleanup_done' not in st.session_state:
        st.session_state.cleanup_done = False

    with st.sidebar:
        st.header("Upload Document")

        # 🔐 NEW: LOGOUT BUTTON
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
        
        uploaded_file_input = st.file_uploader(
            "Choose a document file", 
            type=['pdf', 'txt', 'docx', 'pptx', 'md'],
            accept_multiple_files=False,
            key="file_uploader"
        )
        
        if st.session_state.uploaded_file_object and uploaded_file_input is None:
             st.warning("File is loaded. To upload a new file, clear the current one.")

        if uploaded_file_input and st.sidebar.button("Process Document", use_container_width=True, type="primary"):
            if st.session_state.uploaded_file_object:
                delete_uploaded_file(client, st.session_state.uploaded_file_object)
            
            with st.spinner(f"Processing {uploaded_file_input.name}..."):
                file_obj = upload_document(client, uploaded_file_input)
                
                if file_obj:
                    st.session_state.uploaded_file_object = file_obj
                    st.session_state.messages = []
                    st.session_state.cleanup_done = False
                    st.rerun()

        st.divider()
        st.markdown(
            "**Note on Cleanup:** The file will be deleted from storage when you close the application or upload a new file."
        )
        
        if st.session_state.uploaded_file_object and not st.session_state.cleanup_done:
             if st.button("Manually Delete File from API", use_container_width=True):
                 delete_uploaded_file(client, st.session_state.uploaded_file_object)
                 st.session_state.uploaded_file_object = None
                 st.session_state.cleanup_done = True
                 st.session_state.messages = []
                 st.rerun()

    chat_with_document(client)


if __name__ == "__main__":
    main()