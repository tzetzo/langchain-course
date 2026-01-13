# main.py
import warnings
import streamlit as st
from src.graph import create_graph

# 1. Suppress the Pydantic/Tavily shadowing warnings
warnings.filterwarnings(
    "ignore", message="Field name .* shadows an attribute in parent .*"
)

# 2. Page Configuration
st.set_page_config(
    page_title="LinkedIn Persona AI 2026", 
    page_icon="👤", 
    layout="wide" # Using wide layout to accommodate the image gallery
)

st.title("👤 LinkedIn Summary AI")
st.markdown("Enter a name to find and summarize their professional LinkedIn profile.")

# 3. User Input
typed_name = st.text_input("Enter the full name of the person:", placeholder="e.g. Tsvetan Marinov")

if st.button("Generate Summary") and typed_name:
    app = create_graph()

    with st.status("🔍 Searching and Verifying...", expanded=True) as status:
        initial_state = {
            "person_name": typed_name,
            "raw_data": "",
            "final_json": None,
            "error_count": 0,
            "retry_count": 0,
            "is_verified": False,
        }
        
        result = app.invoke(initial_state)
        
        if result.get("is_verified"):
            status.update(label="✅ Profile Found and Verified!", state="complete")
        else:
            status.update(label="❌ Profile Verification Failed", state="error")

    is_verified = result.get("is_verified", False)
    data = result.get("final_json")
    verified_name = result.get("person_name", typed_name)

    if not is_verified:
        st.error(f"**Verification Failed:** Could not find an exact match for '{typed_name}'.")
        if result.get("raw_data"):
            with st.expander("Review Search Logs"):
                st.write(result["raw_data"])

    elif data:
        # Display Name Match Alert if spellings differ
        if typed_name.strip().lower() != verified_name.strip().lower():
            st.info(f"💡 Found profile for **{verified_name}** (matching your search for '{typed_name}')")

        st.divider()
        
        # 4. Main Profile View
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # We use the image URL determined by the agent
            if data.image_url and data.image_url.startswith("http"):
                st.image(data.image_url, caption="Agent Selected Photo", use_container_width=True)
                st.caption(f"Source: {data.image_url[:50]}...")
            else:
                st.info("No profile photo found.")

        with col2:
            st.subheader(verified_name)
            st.write(data.summary)
            st.markdown("### 📌 Key Facts")
            for fact in data.facts:
                st.write(f"- {fact}")
            st.link_button(f"🔗 View {verified_name}'s Profile", data.linkedin_url, type="primary")

        # 5. Visual Debugger: The Image Gallery
        # This section helps you identify why a photo might be wrong
        st.divider()
        with st.expander("🖼️ Image Verification Gallery (Debug Mode)"):
            st.write("The AI chose the image above from these candidates found in the search results:")
            
            # Try to parse the raw data to find all images
            try:
                import json
                raw_dict = json.loads(result.get("raw_data", "{}"))
                candidate_images = raw_dict.get("images", [])
                
                if candidate_images:
                    cols = st.columns(min(len(candidate_images), 5))
                    for idx, img_url in enumerate(candidate_images):
                        with cols[idx % 5]:
                            st.image(img_url, use_container_width=True)
                            if img_url == data.image_url:
                                st.success("Selected ✅")
                            else:
                                if st.button("Set as Photo", key=f"btn_{idx}"):
                                    # Note: This is a UI-only override for the session
                                    st.session_state["manual_photo"] = img_url
                                    st.rerun()
                else:
                    st.write("No other image candidates found.")
            except:
                st.write("Could not parse image candidates from raw data.")

else:
    st.info("Tip: If the person has a common name, try adding their company (e.g., 'Tsvetan Marinov Netcracker').")