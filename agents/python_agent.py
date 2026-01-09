# python_agent.py

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from e2b_code_interpreter import Sandbox

load_dotenv()

WRITABLE_DIR = "/home/user"   # <-- The ONLY reliable writable directory


@tool
def run_python(code: str) -> str:
    """
    Executes Python code inside an E2B Code Interpreter sandbox.
    Files must be saved to /home/user (the writable directory).
    """
    sandbox = Sandbox.create(api_key=os.environ["E2B_API_KEY"])

    try:
        # Replace any LLM paths with the correct writable directory
        code = code.replace("/workspace", WRITABLE_DIR)
        code = code.replace("/mnt/data", WRITABLE_DIR)
        code = code.replace("/path/to/writable/directory", WRITABLE_DIR)

        # First execution attempt
        execution = sandbox.run_code(code)

        # Detect missing module
        if execution.error and execution.error.name == "ModuleNotFoundError":
            missing = execution.error.value.split("'")[1]

            # Install missing module
            sandbox.run_code(f"pip install {missing}")

            # Retry
            execution = sandbox.run_code(code)

        output = ""

        if execution.logs:
            output += f"LOGS:\n{execution.logs}\n"

        if execution.error:
            output += f"\nERROR:\n{execution.error.traceback}\n"

        # List generated files
        files = sandbox.files.list(WRITABLE_DIR)
        if files:
            output += "\nGenerated files:\n"
            for f in files:
                output += f"- {f.path}\n"

        return output or "Code executed with no output."

    finally:
        sandbox.kill()


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.environ["GROQ_API_KEY"]
)

SYSTEM_PROMPT = f"""
You are a Python coding assistant.
Output ONLY valid Python code.
Do NOT use backticks.
Do NOT use markdown.
Do NOT explain anything.
Do NOT add comments.

IMPORTANT:
- The ONLY writable directory is {WRITABLE_DIR}
- ALWAYS save files to {WRITABLE_DIR}
- Use absolute paths like "{WRITABLE_DIR}/filename.png"
"""


def clean_code(raw: str) -> str:
    code = raw.strip()
    if code.startswith("```"):
        code = code.split("```")[1]
        code = code.replace("python", "", 1)
        code = code.split("```")[0]
    return code.strip()


def python_agent(user_input: str) -> str:
    code_response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ])

    raw_code = code_response.content
    print("RAW LLM OUTPUT:", repr(raw_code))

    code = clean_code(raw_code)

    return run_python.invoke({"code": code})
