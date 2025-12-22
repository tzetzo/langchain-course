# https://smith.langchain.com for tracing
# Requires TAVILY_API_KEY, GROQ_API_KEY, LANGSMITH_API_KEY in .env

import json
import re

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

from schemas import AgentResponse

load_dotenv()

# -------------------------------------------------------------------
# 1. LLM
# -------------------------------------------------------------------
llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # https://console.groq.com/docs/models
    temperature=0.0,
)

# -------------------------------------------------------------------
# 2. Tools
# -------------------------------------------------------------------
tools = [TavilySearch()]
tool_map = {t.name: t for t in tools}

tool_descriptions = "\n".join(f"{t.name}: {t.description}" for t in tools)
tool_names = ", ".join(t.name for t in tools)

def run_tool(name: str, tool_input: str):
    if name not in tool_map:
        return f"Invalid tool: {name}"
    try:
        return tool_map[name].invoke({"query": tool_input})
    except Exception as e:
        return f"Tool error: {e}"

# -------------------------------------------------------------------
# 3. Output schema instructions
# -------------------------------------------------------------------
schema = AgentResponse.model_json_schema()

format_instructions = f"""
Return a JSON object that conforms to this schema:

{json.dumps(schema, indent=2)}

Rules:
- Only output a JSON INSTANCE, not the schema.
- The "answer" field must be a single-line string.
- The "sources" field must be a list of objects with only a "url".
- Do not include markdown, backticks, or explanations.
"""

# -------------------------------------------------------------------
# 4. ReAct Prompt; taken from https://smith.langchain.com/hub/hwchase17/react
# -------------------------------------------------------------------
prompt = ChatPromptTemplate.from_template(
    """
Answer the following question. You have access to the following tools:

{tools}

Use this format:

Question: the question
Thought: reasoning about next step
Action: one of [{tool_names}]
Action Input: input to the action
Observation: tool result
... (repeat as needed)
Thought: I now know the final answer
Final Answer: valid JSON matching these instructions:
{format_instructions}

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
)

# -------------------------------------------------------------------
# 5. Parsing helpers
# -------------------------------------------------------------------
ACTION_RE = re.compile(
    r"Action:\s*(?P<action>[^\n]+)\nAction Input:\s*(?P<input>[^\n]+)",
    re.MULTILINE,
)

JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

# -------------------------------------------------------------------
# 6. ReAct loop (THE AGENT)
# -------------------------------------------------------------------
def react_loop(input_text: str):
    scratchpad = ""
    steps = 0
    max_steps = 8

    formatted = prompt.invoke(
        {
            "input": input_text,
            "tools": tool_descriptions,
            "tool_names": tool_names,
            "format_instructions": format_instructions,
            "agent_scratchpad": scratchpad,
        }
    )

    response = llm.invoke(formatted)
    text = response.content

    while "Final Answer:" not in text and steps < max_steps:
        steps += 1

        match = ACTION_RE.search(text)
        if not match:
            return {"error": "Failed to parse action", "raw_output": text}

        action = match.group("action")
        action_input = match.group("input")

        observation = run_tool(action, action_input)

        scratchpad += (
            f"\nThought:\nAction: {action}\n"
            f"Action Input: {action_input}\n"
            f"Observation: {observation}\n"
        )

        followup = prompt.invoke(
            {
                "input": input_text,
                "tools": tool_descriptions,
                "tool_names": tool_names,
                "format_instructions": format_instructions,
                "agent_scratchpad": scratchpad,
            }
        )

        response = llm.invoke(followup)
        text = response.content

    if steps >= max_steps:
        return {"error": "Max steps exceeded", "raw_output": text}

    # ----------------------------------------------------------------
    # 7. Final JSON extraction + validation
    # ----------------------------------------------------------------
    try:
        final_part = text.split("Final Answer:", 1)[1]
        match = JSON_RE.search(final_part)
        if not match:
            raise ValueError("No JSON object found")

        data = json.loads(match.group())
        parsed = AgentResponse(**data)
        return parsed.model_dump()

    except Exception as e:
        return {"error": f"Failed to parse JSON: {e}", "raw_output": text}

# -------------------------------------------------------------------
# 8. LCEL wrapper
# -------------------------------------------------------------------
chain = RunnableLambda(lambda x: react_loop(x["input"]))

# -------------------------------------------------------------------
# 9. Run
# -------------------------------------------------------------------
result = chain.invoke(
    {
        "input": (
            "Search the web for 3 current AI engineer job postings that mention LangChain, "
            "preferably in the Bay Area, and list their titles, companies, locations, and links."
        )
    }
)

print(result)
