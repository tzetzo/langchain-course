import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from src.state import GraphState
from src.schema import PersonSummary
from utils.scraper import scrape_linkedin_data

load_dotenv()

# Use a specific model version for stability
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.environ["GROQ_API_KEY"],
    temperature=0,
)


# src/nodes.py
import json

def scrape_node(state: GraphState):
    name = state.get("person_name")
    try:
        # Assuming scrape_linkedin_data returns the raw dict from Tavily
        raw_response = scrape_linkedin_data(name) 
        
        # If Tavily returned a dict, we extract and filter images
        if isinstance(raw_response, dict):
            images = raw_response.get("images", [])
            
            # FILTER LOGIC:
            # 1. Profile photos usually contain 'profile-displayphoto'
            # 2. We want to avoid images that look like 'background' or small 'thumbnails'
            profile_photos = [
                img for img in images 
                if "profile-displayphoto" in img and "shrink_200_200" in img
            ]
            
            # 3. If we found specific profile photos, we swap the list
            # If not, we keep the original list as fallback
            if profile_photos:
                raw_response["images"] = profile_photos[:2] # Only give LLM the best 2

        # Convert back to string for the GraphState
        return {"raw_data": json.dumps(raw_response), "error_count": 0}
    except Exception as e:
        return {"raw_data": f"Error: {e}", "error_count": 1}


def summarize_node(state: GraphState):
    raw_info = state.get("raw_data", "")
    person_name = state.get("person_name", "")
    
    structured_llm = llm.with_structured_output(PersonSummary)

    prompt = f"""
    Analyze the following search data for {person_name}:
    {raw_info}

    You must extract the profile picture. 
    INSTRUCTION: Use the VERY FIRST image URL found in the 'images' list. 
    This list has been pre-filtered to ensure it belongs to the profile owner.
    """
    
    summary_obj = structured_llm.invoke(prompt)
    return {"final_json": summary_obj}


import re

def verify_name_node(state: GraphState):
    """
    Verifies that the exact character sequence typed by the user 
    exists within the scraped profile data.
    """
    user_typed_name = state.get("person_name", "").strip()
    # Convert raw_data to string if it isn't already (handles dict/list inputs)
    raw_data_str = str(state.get("raw_data", ""))
    
    print(f"---STRICT VERIFICATION: Checking for '{user_typed_name}'---")

    # 1. CLEAN CHECK: Remove common markdown chars like # or * from data for the check
    clean_data = re.sub(r'[#\*]', '', raw_data_str)
    
    # 2. Case-Insensitive but Letter-Exact Check
    # We check if the exact sequence of letters exists
    if user_typed_name.lower() in clean_data.lower():
        print(f"✅ CHARACTER MATCH: '{user_typed_name}' found in search results.")
        # Even if Python finds it, we let the LLM confirm it's a person and not a 'Liked by' mention
    else:
        print(f"❌ CHARACTER MISMATCH: '{user_typed_name}' not found exactly.")
        return {"is_verified": False}

    # 3. LLM Confirmation (Ensuring the profile belongs to THIS specific name)
    prompt = f"""
    The user is looking for: "{user_typed_name}"
    The search results contain: {raw_data_str[:2000]} 

    Does one of the profiles in the results belong to "{user_typed_name}"?
    - If the name in the results is spelled differently (even one letter), say NO.
    - If the name matches exactly (case-insensitive), say YES.
    
    Answer ONLY with:
    VERDICT: [YES/NO]
    """
    
    response = llm.invoke(prompt).content.strip().upper()
    
    if "VERDICT: YES" in response:
        return {"is_verified": True}
    
    return {"is_verified": False}


def research_optimizer_node(state: GraphState):
    """Refines the search query for a second attempt."""
    print("---OPTIMIZING SEARCH FOR RETRY---")
    name = state["person_name"]
    # We create a more aggressive search query
    enhanced_query = f"{name} LinkedIn official profile professional experience biography"
    
    # We update the person_name temporarily for the scraper to use a better string
    # or you could add a 'search_query' field to the state.
    return {"person_name": enhanced_query, "retry_count": 1}