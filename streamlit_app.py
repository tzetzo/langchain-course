# to run the file:
# streamlit run steamlit_app.py

import streamlit as st
from rag_query import answer_question

st.set_page_config(page_title="RAG Chat", page_icon="💬")

st.title("💬 RAG Chatbot")

def build_history():
    history = ""
    for msg in st.session_state.messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        history += f"{role}: {msg['content']}\n"
    return history

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
user_input = st.chat_input("Ask a question")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message immediately
    with st.chat_message("user"):
        st.write(user_input)

    # Get RAG response
    response = answer_question(user_input, history=build_history())

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Display assistant response
    with st.chat_message("assistant"):
        st.write(response)
