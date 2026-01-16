# Start the app with:
# streamlit run streamlit_app.py

import asyncio
import streamlit as st

from langchain_core.messages import SystemMessage, HumanMessage
from agents.reflection_agent import build_reflection_agent

st.set_page_config(page_title="Reflection Agent", layout="centered")

st.title("🪞 Reflection Agent")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_area("Your prompt", height=120)

max_iterations = st.slider(
    "Reflection depth",
    min_value=1,
    max_value=3,
    value=2,
)

if st.button("Run agent") and user_input.strip():
    graph = build_reflection_agent(max_iterations=max_iterations)

    init_messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=user_input),
    ]

    initial_state = {
        "messages": init_messages,
        "iteration": 0,
    }

    with st.spinner("Thinking..."):
        result = asyncio.run(graph.ainvoke(initial_state))

    st.session_state.history = result["messages"]

# -------------------------
# Output
# -------------------------

if st.session_state.history:
    st.subheader("Conversation")

    for msg in st.session_state.history:
        role = msg.type.capitalize()
        st.markdown(f"**{role}:** {msg.content}")
