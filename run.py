import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables (GROQ_API_KEY, etc.)
load_dotenv()

# Add the current directory to sys.path so Python can find the src module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.mcp_agent.graph import app, initialize_mcp_servers
from src.mcp_agent.mcp_client import mcp_client

async def main():
    try:
        # 1. Initialize and connect to MCP servers (Node.js backend)
        print("🚀 Bootstrapping MCP Servers...")
        await initialize_mcp_servers()
        
        # 2. Prepare the initial state for the LangGraph agent
        # The query asks for both weather and math to trigger both servers
        initial_state = {
            "messages": [
                {"role": "user", "content": "What is the weather in London and what is 25 plus 45?"}
            ]
        }
        
        print("🤖 Agent is thinking...")
        print("-" * 30)

        # 3. Stream the graph execution
        # We use stream_mode="updates" to see the transitions between nodes
        async for event in app.astream(initial_state, stream_mode="updates"):
            for node_name, data in event.items():
                if "messages" in data:
                    last_message = data["messages"][-1]
                    
                    # Determine the source of the message
                    if last_message.type == "ai":
                        role = "🤖 Assistant"
                    elif last_message.type == "tool":
                        role = "🛠️ Tool Result"
                    else:
                        role = "📝 System"

                    # Handle LangChain message objects
                    content = last_message.content
                    
                    # If it's an AI message with tool calls, show them
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        for tool_call in last_message.tool_calls:
                            print(f"\n[{role}]: Calling tool '{tool_call['name']}' with {tool_call['args']}")
                    
                    # Otherwise print the text content
                    elif content:
                        print(f"\n[{role}]: {content}")

    except Exception as e:
        # Detailed error printing for troubleshooting
        print(f"\n❌ Application Error: {type(e).__name__} - {e}")
        # Uncomment the next line if you need the full traceback
        # import traceback; traceback.print_exc()
    
    finally:
        # 4. CRITICAL: Always shut down servers to free up Windows pipes/Node processes
        print("\n" + "-" * 30)
        print("🔌 Shutting down MCP servers...")
        await mcp_client.close_all()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    # Windows-specific event loop policy for subprocesses (Required for MCP)
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Terminated by user.")