# src/graph.py
from langgraph.graph import StateGraph, START, END
from src.state import GraphState
from src.nodes import scrape_node, summarize_node


def should_continue(state: GraphState):
    """
    Decision function: If we have no data, go to END.
    Otherwise, go to the summarizer.
    """
    if not state.get("raw_data") or "No public LinkedIn data" in state["raw_data"]:
        return "end"
    return "continue"


def create_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("scrape_linkedin", scrape_node)
    workflow.add_node("summarize_info", summarize_node)

    workflow.add_edge(START, "scrape_linkedin")

    # Conditional logic
    workflow.add_conditional_edges(
        "scrape_linkedin", should_continue, {"continue": "summarize_info", "end": END}
    )

    workflow.add_edge("summarize_info", END)

    return workflow.compile()
