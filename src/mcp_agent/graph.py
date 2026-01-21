import os
import sys
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import agent_node, tool_node, should_continue
from .mcp_client import mcp_client

# Get the exact Python executable running THIS script
PYTHON_EXE = sys.executable

async def initialize_mcp_servers():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    # We now call 'node' and point to the JavaScript files
    weather_path = os.path.join(root_dir, "mcp_servers", "weather.js")
    calc_path = os.path.join(root_dir, "mcp_servers", "calculator.js")

    try:
        await mcp_client.connect_server("weather", "node", [weather_path])
        await mcp_client.connect_server("calculator", "node", [calc_path])
    except Exception as e:
        raise e

def create_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    return graph.compile()

app = create_graph()