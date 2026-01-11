import streamlit as st
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agents.controller import CodeInterpreterController

st.set_page_config(page_title="QR Batch Generator 2026", layout="wide")

st.title("🚀 AI Batch QR Code Generator")

if "controller" not in st.session_state:
    st.session_state.controller = CodeInterpreterController()

with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    file_bytes = uploaded_file.getvalue() if uploaded_file else None

user_input = st.text_area(
    "What should I generate?", placeholder="Generate 3 QRs for..."
)

if st.button("Run Generator", type="primary"):
    with st.status("Processing...") as status:
        try:
            # We run the controller
            response = st.session_state.controller.run(
                user_input=user_input,
                file_bytes=file_bytes,
                filename=uploaded_file.name if uploaded_file else None,
            )

            # --- Results Layout ---
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Sandbox Output")
                # This helps you see if the AI actually printed the BASE64 markers
                st.text_area("Raw Logs", value=response.logs, height=300)

            with col2:
                st.subheader("Generated Files")
                if not response.files:
                    st.error(
                        "No files found. Check logs to see if the AI printed 'BASE64:' markers."
                    )
                else:
                    for f in response.files:
                        st.write(f"**{f.name}**")
                        if f.name.lower().endswith((".png", ".jpg")):
                            img_stream = io.BytesIO(f.data)
                            img_stream.seek(0)
                            # Updated for 2026 'stretch' syntax
                            st.image(img_stream, width="stretch", output_format="PNG")

                            st.download_button(
                                "Download", f.data, f.name, "image/png", key=f.name
                            )
                        st.divider()

            status.update(label="Complete!", state="complete")
        except Exception as e:
            st.error(f"Error: {e}")
            status.update(label="Failed", state="error")
