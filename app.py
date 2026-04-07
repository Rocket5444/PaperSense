# app.py

import streamlit as st
from engine import initialize_client, upload_document, process_document, delete_uploaded_file


# ================== 🔐 AUTH SYSTEM ==================
def authenticate_user():
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        st.title("🔐 Login Required")

        token = st.text_input("Enter Access Token", type="password")

        if st.button("Login"):
            try:
                correct = st.secrets["APP_AUTH_TOKEN"]
            except Exception:
                st.error("Auth token not set in secrets")
                st.stop()

            if token == correct:
                st.session_state.auth = True
                st.success("Access granted")
                st.rerun()
            else:
                st.error("Invalid token")

        st.stop()


# ================== CHAT ==================
def chat_ui(client):
    if "file" not in st.session_state:
        st.session_state.file = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask something..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                res = process_document(client, st.session_state.file, prompt)
                st.write(res)

        st.session_state.messages.append({"role": "assistant", "content": res})


# ================== MAIN ==================
def main():
    authenticate_user()

    st.set_page_config(page_title="AI Doc Analyzer")
    st.title("📄 AI Document Analyzer")

    client, err = initialize_client()

    if client is None:
        st.error(err)
        return

    with st.sidebar:

        if st.button("Logout"):
            st.session_state.auth = False
            st.rerun()

        file = st.file_uploader("Upload file")

        if file and st.button("Process"):
            obj = upload_document(client, file)
            if obj:
                st.session_state.file = obj
                st.success("File ready!")

        if st.session_state.get("file"):
            if st.button("Delete File"):
                delete_uploaded_file(client, st.session_state.file)
                st.session_state.file = None

    if st.session_state.get("file"):
        chat_ui(client)
    else:
        st.info("Upload a document to begin")


if __name__ == "__main__":
    main()