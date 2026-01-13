import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()


def scrape_linkedin_data(name: str) -> str:
    """
    Uses TavilySearchResults to find LinkedIn profile data.
    Ensures we handle both dictionary and string return types.
    """
    # Use TavilySearch for the most consistent LangChain integration
    search = TavilySearch(max_results=2, search_depth="advanced")

    query = f"site:linkedin.com/in/ '{name}' current position and profile link"

    try:
        results = search.invoke(query)

        # If the tool returns a string (common in some LangChain wrappers)
        if isinstance(results, str):
            return results

        # If the tool returns a list (check if elements are dicts)
        if isinstance(results, list):
            combined_content = []
            for r in results:
                if isinstance(r, dict):
                    # Safely get content or snippet
                    content = r.get("content") or r.get("snippet") or str(r)
                    url = r.get("url", "Unknown Source")
                    combined_content.append(f"Source: {url}\nContent: {content}")
                else:
                    # If the list element is just a string
                    combined_content.append(str(r))

            return "\n\n".join(combined_content)

        return str(results)

    except Exception as e:
        print(f"Scraping error: {e}")
        raise e
