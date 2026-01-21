# Start the app:
# uv run chainlit run app_ui.py -w

import os
import chainlit as cl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing graph and client logic
from src.mcp_agent.graph import app, initialize_mcp_servers
from src.mcp_agent.mcp_client import mcp_client

@cl.on_chat_start
async def start():
    """Runs when the user first opens the UI"""
    try:
        # Show a loading notification in the UI
        msg = cl.Message(content="🚀 Bootstrapping MCP Servers...")
        await msg.send()
        
        await initialize_mcp_servers()
        
        msg.content = "✅ Systems Online. How can I help you today?"
        await msg.update()
    except Exception as e:
        await cl.Message(content=f"❌ Initialization Error: {str(e)}").send()

@cl.on_message
async def main(message: cl.Message):
    """Runs every time the user sends a message"""
    
    # Initialize the graph state with the user's message
    initial_state = {"messages": [{"role": "user", "content": message.content}]}
    
    # We will use this to keep track of the final answer
    final_answer = ""

    # Stream the graph execution
    async for event in app.astream(initial_state, stream_mode="updates"):
        for node_name, data in event.items():
            if "messages" in data:
                last_msg = data["messages"][-1]

                # 1. Handle Tool Calls (The "Thinking" phase)
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    for tool_call in last_msg.tool_calls:
                        # Create a "Step" in Chainlit so the user sees the tool call
                        async with cl.Step(name=f"🛠️ Tool: {tool_call['name']}") as step:
                            step.input = tool_call['args']
                            step.output = "Executing via MCP..."

                # 2. Handle Tool Results (The "Data" phase)
                elif last_msg.type == "tool":
                    # Find the last step and update it with the actual result
                    # Chainlit automatically nests these under the tool call
                    pass # Steps are handled in the tool_calls block above or manually

                # 3. Handle Final AI Response
                elif last_msg.type == "ai" and last_msg.content:
                    final_answer = last_message_content = last_msg.content

    # Send the final response to the user
    await cl.Message(content=final_answer).send()

@cl.on_stop
async def stop():
    """Clean up MCP servers when the user stops the session"""
    await mcp_client.close_all()