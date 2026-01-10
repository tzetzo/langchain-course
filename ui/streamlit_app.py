# Run the app from project root directory with:
# streamlit run ui/streamlit_app.py
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from graph.code_interpreter_graph import run_code_interpreter

st.set_page_config(
    page_title="Code Interpreter",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Code Interpreter")
st.write("Upload a file (optional) and enter your instructions below.")


# ---------------------------------------------------------
# 1. User Input
# ---------------------------------------------------------

user_input = st.text_area(
    "Instructions",
    placeholder="e.g., Load the CSV and summarize it, or run Python code…",
    height=150
)

uploaded_file = st.file_uploader(
    "Upload a file (optional)",
    type=["csv", "txt", "json", "py"]
)

file_bytes = None
filename = None

if uploaded_file:
    file_bytes = uploaded_file.read()
    filename = uploaded_file.name


# ---------------------------------------------------------
# 2. Run Button
# ---------------------------------------------------------

if st.button("Run Code Interpreter"):
    if not user_input.strip():
        st.error("Please enter instructions before running.")
    else:
        with st.spinner("Running…"):
            response = run_code_interpreter(
                user_input=user_input,
                file_bytes=file_bytes,
                filename=filename
            )

        # ---------------------------------------------------------
        # 3. Display Logs
        # ---------------------------------------------------------

        st.subheader("Logs")
        st.code(response.logs, language="text")

        # ---------------------------------------------------------
        # 4. Display Generated Files
        # ---------------------------------------------------------

        if response.files:
            st.subheader("Generated Files")

            for fpath in response.files:
                # Skip system files
                if any(x in fpath for x in [".bashrc", ".profile", ".bash_logout"]):
                    continue

                # Read file from sandbox via controller logs
                st.write(f"📄 {fpath}")

                # Download button
                try:
                    with open(fpath, "rb") as f:
                        st.download_button(
                            label=f"Download {fpath.split('/')[-1]}",
                            data=f.read(),
                            file_name=fpath.split("/")[-1]
                        )
                except Exception:
                    st.warning(f"Unable to load file: {fpath}")
