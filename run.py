# Start app:
# uv run python run.py

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.mcp_agent.graph import app, initialize_mcp_servers
from src.mcp_agent.mcp_client import mcp_client

async def main():
    try:
        # 1. Initialize MCP servers
        print("🚀 Bootstrapping MCP Servers (Weather & Calculator)...")
        await initialize_mcp_servers()
        
        print("\n✅ System Ready! Type 'exit' to quit.")
        print("-" * 50)

        while True:
            # 2. Get dynamic user input
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("👋 Goodbye!")
                break

            # 3. Prepare state for this specific turn
            initial_state = {"messages": [{"role": "user", "content": user_input}]}
            
            print("🤖 Agent is thinking...")

            # 4. Stream the execution for the current query
            async for event in app.astream(initial_state, stream_mode="updates"):
                for node_name, data in event.items():
                    if "messages" in data:
                        last_message = data["messages"][-1]
                        
                        # Determine role for beautiful UI
                        if last_message.type == "ai":
                            role = "🤖 Assistant"
                        elif last_message.type == "tool":
                            role = "🛠️ Tool Result"
                        else:
                            role = "📝 System"

                        # Show tool calls specifically
                        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                print(f"\n[{role}]: Calling '{tool_call['name']}' with {tool_call['args']}")
                        
                        # Print final text content
                        elif last_message.content:
                            print(f"\n[{role}]: {last_message.content}")

    except Exception as e:
        print(f"\n❌ Application Error: {type(e).__name__} - {e}")
    
    finally:
        # 5. Cleanup
        print("\n" + "-" * 50)
        print("🔌 Shutting down MCP servers...")
        await mcp_client.close_all()
        print("✅ Shutdown complete.")

if __name__ == "__main__":
    # Windows-specific fix for Stdio/Pipes
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass