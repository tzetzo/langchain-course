# main.py
import warnings

# Suppress the Pydantic/Tavily shadowing warnings
warnings.filterwarnings(
    "ignore", message="Field name .* shadows an attribute in parent .*"
)

import streamlit as st
from src.graph import create_graph

st.set_page_config(page_title="LinkedIn Persona AI", page_icon="👤")
st.title("👤 LinkedIn Summary AI")

name = st.text_input("Enter the full name of the person:")

if st.button("Generate Summary") and name:
    app = create_graph()

    with st.status("🔍 Searching and Analyzing...", expanded=True) as status:
        # Invoke the graph
        initial_state = {
            "person_name": name,
            "raw_data": "",
            "final_json": None,
            "error_count": 0,
        }
        result = app.invoke(initial_state)
        status.update(label="✅ Analysis Complete!", state="complete")

    # Display JSON results in a clean UI
    # Inside the result display section of main.py
    data = result["final_json"]

    if data:
        st.subheader(f"Results for {name}")
        st.write(data.summary)

        st.markdown("### 📌 Key Facts")
        for fact in data.facts:
            st.write(f"- {fact}")

        # Add a clickable link
        st.divider()
        st.link_button("🔗 View LinkedIn Profile", data.linkedin_url)

        with st.expander("View Raw JSON"):
            st.json(data.model_dump())
