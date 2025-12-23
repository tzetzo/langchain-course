import json

from dotenv import load_dotenv
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

from schemas import AgentResponse

load_dotenv()

# ------------------------------------------------------------
# 1. LLM (tool-calling enabled)
# ------------------------------------------------------------
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.0,
)

# ------------------------------------------------------------
# 2. Tools
# ------------------------------------------------------------
tools = [TavilySearch()]

llm_with_tools = llm.bind_tools(tools)


# ------------------------------------------------------------
# 3. Prompt (NO ReAct)
# ------------------------------------------------------------
def escape_curly_braces(text: str) -> str:
    return text.replace("{", "{{").replace("}", "}}")


schema = escape_curly_braces(json.dumps(AgentResponse.model_json_schema(), indent=2))

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an AI assistant that may call tools to gather information. "
            "Use tools when needed. When you are done, return ONLY valid JSON "
            "matching this schema:\n\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Rules:\n"
            "- Output ONLY a JSON instance\n"
            "- No markdown, no backticks\n"
            "- The answer must be concise\n",
        ),
        ("human", "{input}"),
    ]
)


# ------------------------------------------------------------
# 4. Tool-calling loop (agent runtime)
# ------------------------------------------------------------
def tool_calling_loop(input_text: str):
    messages = prompt.invoke({"input": input_text}).to_messages()

    while True:
        response = llm_with_tools.invoke(messages)

        # Case 1: model wants to call a tool
        if response.tool_calls:
            messages.append(response)

            for call in response.tool_calls:
                tool_name = call["name"]
                tool_args = call["args"]
                tool_call_id = call["id"]

                tool = next(t for t in tools if t.name == tool_name)
                observation = tool.invoke(tool_args)

                messages.append(
                    ToolMessage(
                        content=json.dumps(observation),
                        tool_call_id=tool_call_id,
                    )
                )
            continue

        # Case 2: final answer
        try:
            data = json.loads(response.content)
            parsed = AgentResponse(**data)
            return parsed.model_dump()
        except Exception as e:
            return {
                "error": f"Invalid final JSON: {e}",
                "raw_output": response.content,
            }


# ------------------------------------------------------------
# 5. LCEL wrapper
# ------------------------------------------------------------
chain = RunnableLambda(lambda x: tool_calling_loop(x["input"]))

# ------------------------------------------------------------
# 6. Run
# ------------------------------------------------------------
result = chain.invoke(
    {
        "input": (
            "Search the web for 3 current AI engineer job postings that mention LangChain, "
            "preferably in the Bay Area, and list their titles, companies, locations, and links."
        )
    }
)

print(result)
