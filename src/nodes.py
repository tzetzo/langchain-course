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


def scrape_node(state: GraphState):
    """Node 1: Scrape LinkedIn."""
    name = state.get("person_name")
    try:
        data = scrape_linkedin_data(name)
        # Ensure we return a dict that matches the GraphState keys exactly
        return {"raw_data": data, "error_count": 0}
    except Exception as e:
        print(f"Scrape Node Error: {e}")
        return {"raw_data": "Error fetching data.", "error_count": 1}


def summarize_node(state: GraphState):
    """Node 2: Convert raw data into structured JSON."""
    # Safety check: get() prevents KeyError if the previous node failed
    raw_info = state.get("raw_data", "No data available")
    person_name = state.get("person_name", "Unknown")

    structured_llm = llm.with_structured_output(PersonSummary)

    prompt = f"""
    You are a professional researcher. Based on the following search results:
    {raw_info}
    
    Task:
    1. Write a 2-3 sentence summary for {person_name}.
    2. Identify 3 interesting professional facts.
    3. Extract the exact LinkedIn Profile URL for this person.
    4. A profile image URL from the 'images' list in the data.
    
    If multiple URLs are present, choose the one that best matches a personal profile (linkedin.com/in/...).
    """

    try:
        summary_obj = structured_llm.invoke(prompt)
        return {"final_json": summary_obj}
    except Exception as e:
        print(f"Summarize Node Error: {e}")
        # Return a fallback object so the frontend doesn't crash
        fallback = PersonSummary(
            summary="Could not generate summary.", facts=["N/A", "N/A", "N/A"]
        )
        return {"final_json": fallback}
