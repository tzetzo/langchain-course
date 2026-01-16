import asyncio
from agents.reflection_agent import build_reflection_agent
from langgraph.graph import MessagesState, START, END
from langchain_core.messages import SystemMessage, HumanMessage

async def main():
    graph = build_reflection_agent()
    # Optional: visualize the graph structure
    graph.get_graph().draw_mermaid_png(output_file_path="graph.png")

    # initial user message
    init_messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="Explain recursion like I'm five.")
    ]

    initial_state = {
        "messages": init_messages,
        "iteration": 0
    }

    # run graph
    result = await graph.ainvoke(initial_state)
    print("Final output:", result["messages"])

if __name__ == "__main__":
    asyncio.run(main())
