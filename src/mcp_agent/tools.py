"""Convert MCP tools to LangChain tools with Pydantic v2 compatibility"""
from typing import Any, List
from langchain_core.tools import BaseTool
from pydantic import Field, create_model
from .mcp_client import mcp_client

class MCPToolWrapper(BaseTool):
    """Wrapper to convert MCP tools to LangChain tools"""
    
    server_name: str
    mcp_tool_name: str
    
    def _run(self, **kwargs: Any) -> str:
        raise NotImplementedError("MCP tools must be run asynchronously via _arun.")
    
    async def _arun(self, **kwargs: Any) -> Any:
        """Execute the MCP tool via the central client"""
        # We pass only the tool name and arguments; the client routes to the server
        result = await mcp_client.call_tool(self.mcp_tool_name, kwargs)
        
        # Handle the standardized MCP Content blocks (TextContent, etc.)
        if hasattr(result, 'content'):
            return "\n".join([block.text for block in result.content if hasattr(block, 'text')])
        return str(result)

async def create_langchain_tools_from_mcp() -> List[BaseTool]:
    """Create LangChain tools from all connected MCP servers"""
    mcp_metadata_list = await mcp_client.get_combined_tools() 
    langchain_tools = []
    
    for item in mcp_metadata_list:
        server_name = item["server"]
        tool_obj = item["tool"]  # This is the Pydantic Tool object from the SDK
        
        # FIX: Use attribute access (.name, .description) instead of ["name"]
        mcp_name = tool_obj.name
        mcp_desc = tool_obj.description
        # inputSchema is also an attribute of the Tool object
        mcp_schema = tool_obj.inputSchema if hasattr(tool_obj, "inputSchema") else {}
        
        # Dynamic Pydantic model creation for LangChain's args_schema
        properties = mcp_schema.get("properties", {})
        required = mcp_schema.get("required", [])
        
        fields = {}
        for prop_name, prop_schema in properties.items():
            field_type = str if prop_schema.get("type") == "string" else float
            is_required = prop_name in required
            fields[prop_name] = (
                field_type,
                Field(default=... if is_required else None, description=prop_schema.get("description", ""))
            )
        
        InputModel = create_model(f"{mcp_name}Schema", **fields)
        
        # Construct the LangChain-compatible tool
        tool = MCPToolWrapper(
            name=mcp_name,
            description=mcp_desc,
            server_name=server_name,
            mcp_tool_name=mcp_name,
            args_schema=InputModel
        )
        langchain_tools.append(tool)
    
    return langchain_tools