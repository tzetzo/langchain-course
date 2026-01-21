"""Graph node functions updated for MCP compatibility and Groq type-fixing"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage, SystemMessage
from .state import AgentState
from .mcp_client import mcp_client
from .tools import create_langchain_tools_from_mcp

load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0
)

# Define the System Instructions to fix the "String vs Number" hallucination
SYSTEM_INSTRUCTIONS = SystemMessage(content=(
    "You are a precise mathematical and weather assistant. "
    "CRITICAL: When using the 'calculate' tool, you MUST pass the arguments 'a' and 'b' "
    "as raw numbers (e.g., 10.5 or -5), NOT as strings (e.g., '10.5'). "
    "If you must use a negative number, ensure it is a JSON number."
))

async def agent_node(state: AgentState) -> AgentState:
    """Main agent node that uses LLM with MCP tools and system instructions"""
    # 1. Get MCP tools
    tools = await create_langchain_tools_from_mcp()
    llm_with_tools = llm.bind_tools(tools)
    
    # 2. Prepend system instructions to the message history
    # This guides the LLM to use the correct types for Groq's validator
    messages = [SYSTEM_INSTRUCTIONS] + state["messages"]
    
    # 3. Invoke LLM
    response = await llm_with_tools.ainvoke(messages)
    
    return {"messages": [response]}

async def tool_node(state: AgentState) -> AgentState:
    """Execute tool calls using the MCP Client routing logic"""
    last_message = state["messages"][-1]
    new_messages = []
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"  --> Executing tool: {tool_name}")
            
            try:
                # ROUTE TO MCP
                result = await mcp_client.call_tool(tool_name, tool_args)
                
                # PARSE RESULTS
                content = ""
                if hasattr(result, 'content'):
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
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return "end"