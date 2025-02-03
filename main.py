import streamlit as st
import requests
import os
import json
import re

# Backend API URLs
INGESTION_URL = "http://13.211.139.40/api/Ingestion_File"
CHAT_URL = "http://13.211.139.40/api/chat-bot"

def is_valid_uuid(uuid_str):
    """Validates if a string is a valid UUID."""
    uuid_regex = re.compile(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$')
    return bool(uuid_regex.match(uuid_str))

def ingest_file(file, chatbot_id, user_id):
    """Handles file ingestion API request."""
    files = {"files": (file.name, file, "application/pdf")}
    data = {
        "llm": "openai",
        "chatbot_id": chatbot_id,
        "chunk_size": "1000",
        "chunk_overlap": "100",
        "embeddings_model": "openai",
        "vectorstore_name": "pgvector"
    }
    response = requests.post(INGESTION_URL, files=files, data=data)
    return response.json(), response.status_code

def chat_with_bot(query, chatbot_id, user_id):
    """Handles chat API request."""
    data = {
        "query": query,
        "chatbot_id": chatbot_id,
        "user_id": user_id
    }
    response = requests.post(CHAT_URL, json=data)
    return response.json()

# Streamlit UI
st.set_page_config(page_title="Arabic Bot", layout="wide")
st.title("Arabic Bot")

# Sidebar - File Upload & User Details
st.sidebar.header("Upload File & Enter Details")
chatbot_id = st.sidebar.text_input("Chatbot ID")
user_id = st.sidebar.text_input("User ID")
uploaded_file = st.sidebar.file_uploader("Upload a PDF File", type=["pdf"])

if chatbot_id and not is_valid_uuid(chatbot_id):
    st.sidebar.error("Invalid Chatbot ID. Please enter a valid UUID.")
    chatbot_id = None

# Initialize session state variables if not present
if "ingested" not in st.session_state:
    st.session_state.ingested = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if uploaded_file and chatbot_id and user_id:
    if not st.session_state.ingested:
        with st.spinner("Ingesting file..."):
            response, status_code = ingest_file(uploaded_file, chatbot_id, user_id)
            if response.get("message") == "Ingestion Successful!":
                st.session_state.ingested = True
                st.success("File ingested successfully!")
            else:
                st.error(f"File ingestion failed. Full Response: {json.dumps(response, indent=2)}, Status Code: {status_code}")
    ingested = st.session_state.ingested
else:
    ingested = False
    st.sidebar.warning("Please upload a file and enter Chatbot ID & User ID.")

# Chat Screen (Only available after file ingestion)
if ingested:
    st.subheader("💬 Chat with Arabic Bot")
    user_query = st.text_input("Ask something:")
    if st.button("Send") and user_query:
        with st.spinner("Fetching response..."):
            response = chat_with_bot(user_query, chatbot_id, user_id)
            bot_reply = response.get("data", "No response from bot.").get("response", "No response from bot.")
            
            st.session_state.chat_history.append(("You", user_query))
            st.session_state.chat_history.append(("Bot", bot_reply))
    
    # Display Chat History with user on right and bot on left
    for speaker, message in st.session_state.chat_history:
        if speaker == "You":
            col1, col2 = st.columns([1, 4])
            with col2:
                st.markdown(f"<div style='text-align: right; background-color: #d1e7dd; padding: 10px; border-radius: 10px;'>{message}</div>", unsafe_allow_html=True)
        else:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"<div style='text-align: left; background-color: #B7C9E2; padding: 10px; border-radius: 10px;'>{message}</div>", unsafe_allow_html=True)
else:
    st.info("Upload a file and provide details to start chatting.")
