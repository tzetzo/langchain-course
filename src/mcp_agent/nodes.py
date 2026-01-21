"""Graph node functions updated for MCP compatibility"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage
from .state import AgentState
from .mcp_client import mcp_client  # Ensure this import is correct
from .tools import create_langchain_tools_from_mcp

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0
)

async def agent_node(state: AgentState) -> AgentState:
    """Main agent node that uses LLM with MCP tools"""
    # 1. Get MCP tools using the updated client method
    # This uses the 'list_all_tools' alias we added to mcp_client.py
    tools = await create_langchain_tools_from_mcp()
    llm_with_tools = llm.bind_tools(tools)
    
    # 2. Invoke LLM with current message history
    response = await llm_with_tools.ainvoke(state["messages"])
    
    return {"messages": [response]}

async def tool_node(state: AgentState) -> AgentState:
    """Execute tool calls using the MCP Client routing logic"""
    last_message = state["messages"][-1]
    new_messages = []
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # 1. Get the list of tools
        tools = await create_langchain_tools_from_mcp()
        # 2. Map tools by their .name attribute (NOT subscriptable dictionary access)
        tool_map = {tool.name: tool for tool in tools}
        
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"  --> Executing tool: {tool_name}")
            
            try:
                # 3. ROUTE TO MCP: Use our custom call_tool method from mcp_client.py
                result = await mcp_client.call_tool(tool_name, tool_args)
                
                # 4. PARSE RESULTS: Extract text blocks from the MCP response
                # MCP results often come as a list of content blocks
                content = ""
                if hasattr(result, 'content'):
                    # MCP content blocks usually have a .text attribute
                    content = "\n".join([block.text for block in result.content if hasattr(block, 'text')])
                else:
                    content = str(result)

                new_messages.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=content,
                    name=tool_name
                ))
            except Exception as e:
                print(f"❌ Error executing {tool_name}: {e}")
                new_messages.append(ToolMessage(
                    tool_call_id=tool_call["id"],
                    content=f"Error: {str(e)}",
                    name=tool_name
                ))
    
    return {"messages": new_messages}

def should_continue(state: AgentState) -> str:
    """Decide whether to continue to tools or end"""
    last_message = state["messages"][-1]
    
    # Check if the AI wants to call tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "end"