# https://smith.langchain.com to see how the prompt and agent execution happens!
# Must have TAVILY_API_KEY, GROQ_API_KEY, LANGSMITH_TRACING/API_KEY/PROJECT in .env

import json

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch

from schemas import AgentResponse

load_dotenv()

# 1. LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # https://console.groq.com/docs/models
    temperature=0.0,
)

# 2. Tools
tools = [TavilySearch()]
tool_map = {t.name: t for t in tools}

tool_descriptions = "\n".join([f"{t.name}: {t.description}" for t in tools])
tool_names = ", ".join([t.name for t in tools])

# ✅ Auto-generate format instructions WITHOUT repeating schema manually
schema = AgentResponse.model_json_schema()

format_instructions = f"""
Return a JSON object that conforms to this schema:

{json.dumps(schema, indent=2)}

Rules:
- Only output a JSON INSTANCE, not the schema.
- The "answer" field must be a single-line string with no newlines, no markdown, and no backslashes.
- The "sources" field must be a list of objects, each containing only a "url" field.
- Do not include markdown or backticks.
"""

# 3. ReAct Prompt; taken from https://smith.langchain.com/hub/hwchase17/react
prompt = ChatPromptTemplate.from_template(
    """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question formatted as valid JSON matching these instructions:
{format_instructions}

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
)


# 4. Multi-step ReAct loop
def react_loop(input_text):
    # Build initial prompt
    formatted = prompt.invoke(
        {
            "input": input_text,
            "tools": tool_descriptions,
            "tool_names": tool_names,
            "format_instructions": format_instructions,
            "agent_scratchpad": "",
        }
    )
    # First LLM call
    response = llm.invoke(formatted)
    text = response.content

    max_steps = 8
    steps = 0
    # Loop until Final Answer
    while "Final Answer:" not in text and steps < max_steps:
        steps += 1
        # Try to parse Action and Action Input
        try:
            action = text.split("Action:")[1].split("\n")[0].strip()
            action_input = text.split("Action Input:")[1].split("\n")[0].strip()
        except Exception:
            # If parsing fails, break
            return text
        # Run the tool
        if action in tool_map:
            observation = tool_map[action].invoke({"query": action_input})
        else:
            observation = f"Unknown tool: {action}"
        # Feed back into the model
        followup_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "Continue the ReAct reasoning."),
                ("assistant", text),
                ("human", f"Observation: {observation}"),
            ]
        )

        response = llm.invoke(followup_prompt.format())
        text = response.content

    # ✅ Extract JSON after "Final Answer:"
    try:
        json_str = text.split("Final Answer:")[1].strip()
        data = json.loads(json_str)
        parsed = AgentResponse(**data)
        return parsed.model_dump()
    except Exception as e:
        return {"error": f"Failed to parse JSON: {e}", "raw_output": text}


# 5. LCEL wrapper
chain = RunnableLambda(lambda x: react_loop(x["input"]))

# 6. Run
result = chain.invoke(
    {
        "input": "search the web for 3 current AI engineer job postings that mention LangChain, "
        "preferably in the Bay Area, and list their titles, companies, locations, and links. "
        "If LinkedIn links are not available or valid, use other job boards."
    }
)

print(result)
