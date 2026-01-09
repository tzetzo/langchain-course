# csv_agent.py

import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from e2b_code_interpreter import Sandbox

load_dotenv()

WRITABLE_DIR = "/home/user"   # The sandbox's writable directory


# ---------------------------------------------------------
# 1. CSV Execution Tool
# ---------------------------------------------------------

@tool
def run_csv_task(csv_bytes: bytes, csv_filename: str, code: str) -> str:
    """
    Executes CSV-related Python code inside an E2B Code Interpreter sandbox.
    Writes the uploaded CSV into the sandbox before running the code.
    Files must be saved to /home/user (the writable directory).
    """
    sandbox = Sandbox.create(api_key=os.environ["E2B_API_KEY"])

    try:
        # Write uploaded CSV into the sandbox
        input_path = f"{WRITABLE_DIR}/{csv_filename}"
        sandbox.files.write(input_path, csv_bytes)

        # Rewrite any incorrect paths in LLM code
        code = code.replace("/workspace", WRITABLE_DIR)
        code = code.replace("/mnt/data", WRITABLE_DIR)
        code = code.replace("/path/to/writable/directory", WRITABLE_DIR)

        # First execution attempt
        execution = sandbox.run_code(code)

        # Detect missing module
        if execution.error and execution.error.name == "ModuleNotFoundError":
            missing = execution.error.value.split("'")[1]
            sandbox.run_code(f"pip install {missing}")
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

        return output or "CSV task executed with no output."

    finally:
        sandbox.kill()


# ---------------------------------------------------------
# 2. LLM that writes CSV‑related Python code ONLY
# ---------------------------------------------------------

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    groq_api_key=os.environ["GROQ_API_KEY"]
)

SYSTEM_PROMPT = f"""
You are a CSV analysis assistant.
Output ONLY valid Python code.
Do NOT use backticks.
Do NOT use markdown.
Do NOT explain anything.
Do NOT add comments.

IMPORTANT:
- Use pandas for all CSV operations.
- The uploaded CSV file will be located at {WRITABLE_DIR}/<csv_filename>
- The ONLY writable directory is {WRITABLE_DIR}
- ALWAYS save output CSV files to {WRITABLE_DIR}
- Use absolute paths like "{WRITABLE_DIR}/output.csv"
"""


# ---------------------------------------------------------
# 3. Clean code
# ---------------------------------------------------------

def clean_code(raw: str) -> str:
    code = raw.strip()
    if code.startswith("```"):
        code = code.split("```")[1]
        code = code.replace("python", "", 1)
        code = code.split("```")[0]
    return code.strip()


# ---------------------------------------------------------
# 4. Agent function
# ---------------------------------------------------------

def csv_agent(user_input: str, csv_bytes: bytes, csv_filename: str) -> str:
    """
    Main entry point for the CSV agent.
    1. LLM writes Python code for CSV analysis
    2. Code is executed in E2B sandbox
    3. Output is returned
    """
    code_response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"CSV filename: {csv_filename}\n\nTask: {user_input}")
    ])

    raw_code = code_response.content
    print("RAW LLM OUTPUT:", repr(raw_code))

    code = clean_code(raw_code)

    return run_csv_task.invoke({
        "csv_bytes": csv_bytes,
        "csv_filename": csv_filename,
        "code": code
    })
