"""Agent State Definition"""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the MCP agent"""
    messages: Annotated[list, add_messages]