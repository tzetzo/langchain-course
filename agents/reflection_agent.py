import os
from dotenv import load_dotenv
from typing import TypedDict, List

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq

load_dotenv()

# -------------------------
# LLMs
# -------------------------

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.environ["GROQ_API_KEY"],
    temperature=0.2,
)

critic = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.environ["GROQ_API_KEY"],
    temperature=0.0,
)

# -------------------------
# State
# -------------------------

class AgentState(TypedDict):
    messages: List[BaseMessage]
    iteration: int

# -------------------------
# Nodes
# -------------------------

async def generate(state: AgentState) -> AgentState:
    response = await llm.ainvoke(state["messages"])
    return {
        "messages": state["messages"] + [response],
        "iteration": state["iteration"],
    }

async def reflect(state: AgentState) -> AgentState:
    critique = await critic.ainvoke(
        state["messages"]
        + [HumanMessage(content="Critique the last answer and suggest improvements.")]
    )
    return {
        "messages": state["messages"] + [critique],
        "iteration": state["iteration"] + 1,
    }

# -------------------------
# Graph
# -------------------------

def build_reflection_agent(max_iterations: int = 2):
    graph = StateGraph(AgentState)

    graph.add_node("generate", generate)
    graph.add_node("reflect", reflect)

    graph.set_entry_point("generate")

    graph.add_edge("generate", "reflect")

    graph.add_conditional_edges(
        "reflect",
        lambda s: END if s["iteration"] >= max_iterations else "generate",
    )

    return graph.compile()
