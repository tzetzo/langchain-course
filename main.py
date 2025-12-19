# https://smith.langchain.com to see how the prompt and agent execution happens! 
# Must have TAVILY_API_KEY, GROQ_API_KEY, LANGSMITH_TRACING/API_KEY/PROJECT in .env

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

load_dotenv()

# 1. LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile", # https://console.groq.com/docs/models
    temperature=0.0,
)

# 2. Tools
tools = [TavilySearch()]
tool_map = {t.name: t for t in tools}

tool_descriptions = "\n".join([t.description for t in tools])
tool_names = ", ".join([t.name for t in tools])

# 3. ReAct Prompt; taken from https://smith.langchain.com/hub/hwchase17/react
prompt = ChatPromptTemplate.from_template("""
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
Final Answer: the final answer to the original input question

Begin!

Question: {input}
""")

# 4. Multi-step ReAct loop
def react_loop(input_text):
    # Build initial prompt
    formatted = prompt.invoke({
        "input": input_text,
        "tools": tool_descriptions,
        "tool_names": tool_names,
    })

    # First LLM call
    response = llm.invoke(formatted)
    text = response.content

    # Loop until Final Answer
    while "Final Answer:" not in text:
        # Try to parse Action and Action Input
        try:
            action = text.split("Action:")[1].split("\n")[0].strip()
            action_input = text.split("Action Input:")[1].split("\n")[0].strip()
        except:
            # If parsing fails, break
            return text

        # Run the tool
        if action in tool_map:
            observation = tool_map[action].invoke({"query": action_input})
        else:
            observation = f"Unknown tool: {action}"

        # Feed back into the model
        followup_prompt = ChatPromptTemplate.from_messages([
            ("system", "Continue the ReAct reasoning."),
            ("assistant", text),
            ("human", f"Observation: {observation}")
        ])

        response = llm.invoke(followup_prompt.format())
        text = response.content

    return text

# 5. LCEL wrapper
chain = RunnableLambda(lambda x: react_loop(x["input"]))

# 6. Run
result = chain.invoke({
    "input": "search for 3 job postings for an AI engineer using LangChain in the Bay Area on LinkedIn and list their links"
})

print(result)
