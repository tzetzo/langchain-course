# code_interpreter_graph.py

from typing import Optional, TypedDict
from langgraph.graph import StateGraph, END

from agents.controller import CodeInterpreterController, ControllerResponse


# ---------------------------------------------------------
# 1. Define the graph state
# ---------------------------------------------------------

class GraphState(TypedDict, total=False):
    user_input: str
    file_bytes: Optional[bytes]
    filename: Optional[str]
    controller_response: Optional[ControllerResponse]


# ---------------------------------------------------------
# 2. Nodes
# ---------------------------------------------------------

def input_node(state: GraphState) -> GraphState:
    """
    Initial node — simply passes the input state forward.
    """
    return state


def controller_node(state: GraphState) -> GraphState:
    """
    Calls the controller and stores the response.
    """
    controller = CodeInterpreterController()

    response = controller.run(
        user_input=state["user_input"],
        file_bytes=state.get("file_bytes"),
        filename=state.get("filename")
    )

    state["controller_response"] = response
    return state


def output_node(state: GraphState) -> GraphState:
    """
    Final node — returns the state as-is.
    """
    return state


# ---------------------------------------------------------
# 3. Build the graph
# ---------------------------------------------------------

def create_code_interpreter_graph():
    graph = StateGraph(GraphState)

    graph.add_node("input", input_node)
    graph.add_node("controller", controller_node)
    graph.add_node("output", output_node)

    graph.set_entry_point("input")

    graph.add_edge("input", "controller")
    graph.add_edge("controller", "output")
    graph.add_edge("output", END)

    return graph.compile()


# ---------------------------------------------------------
# 4. Helper for running the graph
# ---------------------------------------------------------

def run_code_interpreter(user_input: str, file_bytes: bytes | None = None, filename: str | None = None):
    graph = create_code_interpreter_graph()

    initial_state: GraphState = {
        "user_input": user_input,
        "file_bytes": file_bytes,
        "filename": filename
    }

    final_state = graph.invoke(initial_state)
    return final_state["controller_response"]
