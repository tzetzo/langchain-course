# src/graph.py
from langgraph.graph import StateGraph, START, END
from src.state import GraphState
from src.nodes import scrape_node, summarize_node, verify_name_node, research_optimizer_node

def should_continue(state: GraphState):
    if state.get("is_verified"):
        return "summarize"
    
    # If not verified and we haven't retried yet, try optimizing
    if state.get("retry_count", 0) < 1:
        return "retry"
    
    # If we already retried and still failed, give up
    return "end"

def create_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("scrape_linkedin", scrape_node)
    workflow.add_node("verify_name", verify_name_node)
    workflow.add_node("optimize_search", research_optimizer_node) # NEW
    workflow.add_node("summarize_info", summarize_node)

    workflow.add_edge(START, "scrape_linkedin")
    workflow.add_edge("scrape_linkedin", "verify_name")

    workflow.add_conditional_edges(
        "verify_name",
        should_continue,
        {
            "summarize": "summarize_info",
            "retry": "optimize_search", # Loop back
            "end": END
        }
    )

    # The magic loop: Optimizer goes back to Scraper
    workflow.add_edge("optimize_search", "scrape_linkedin")
    workflow.add_edge("summarize_info", END)

    return workflow.compile()