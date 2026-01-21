import asyncio
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self):
        self.sessions = {}
        self.exit_stack = None
    
    async def connect_server(self, name: str, command: str, args: list[str]):
        if self.exit_stack is None:
            self.exit_stack = AsyncExitStack()

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        server_params = StdioServerParameters(command=command, args=args, env=env)
        
        try:
            print(f"  --> Connecting to {name} (Node.js)...")
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = transport
            
            session = ClientSession(read, write)
            await self.exit_stack.enter_async_context(session)
            
            # This implementation object is crucial for Pydantic compatibility on Windows
            client_info = types.Implementation(
                name="mcp-agent-python",
                version="1.0.0"
            )
            
            print(f"  --> Initializing {name}...")
            await asyncio.wait_for(session.initialize(), timeout=10.0)
            
            self.sessions[name] = session
            print(f"✅ {name} server ready.")
            
        except Exception as e:
            print(f"❌ {name} failed: {type(e).__name__} - {e}")
            raise

    # ALIAS for list_all_tools to satisfy your LangGraph nodes
    async def list_all_tools(self):
        """Standardized method name for LangGraph nodes to find."""
        return await self.get_combined_tools()

    async def get_combined_tools(self) -> list:
        """Fetch all tools from all connected MCP servers."""
        combined_tools = []
        for name, session in self.sessions.items():
            # session.list_tools() returns a ListToolsResult object
            result = await session.list_tools()
            
            # result.tools is a list of Tool objects (Pydantic models)
            for tool in result.tools:
                # We store as a dict so tools.py knows which server owns which tool
                combined_tools.append({
                    "server": name,
                    "tool": tool
                })
        return combined_tools

    async def call_tool(self, tool_name: str, arguments: dict):
        """
        Routes the tool call to the correct server by searching 
        which session owns the tool.
        """
        for name, session in self.sessions.items():
            # Check if this server has the tool
            tools_result = await session.list_tools()
            if any(t.name == tool_name for t in tools_result.tools):
                # Execute the tool on this specific session
                return await session.call_tool(tool_name, arguments)
        
        raise ValueError(f"Tool '{tool_name}' not found on any connected server.")

    async def close_all(self):
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.exit_stack = None
            self.sessions.clear()

mcp_client = MCPClient()