import os
import re
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

WRITABLE_DIR = "/home/user"
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = f"""
You are a Data Analysis Assistant. You have access to a CSV at {{csv_path}}.

### BEGIN CODE

Rules:
1. ANALYZE FIRST: If the user asks a question about the data (e.g., "how many rows?", "what are the columns?"), simply write pandas code to answer the question using `print()`.
2. QR GENERATION: ONLY generate QR codes if the user explicitly requests them (e.g., "Generate QRs for these links").
3. BATCH PROTOCOL (If QRs requested):
   Use the Base64 printing method:
   print(f"FILENAME:{{fname}}\\nBASE64:{{b64_str}}")

4. Data Access: `df = pd.read_csv('{{csv_path}}')`.
"""


def extract_code_from_llm_output(text: str) -> str:
    """
    Highly resilient code extraction.
    Prioritizes markers, falls back to markdown, and finally to raw text.
    """
    # 1. Try our custom marker
    if "### BEGIN CODE" in text:
        text = text.split("### BEGIN CODE")[-1]

    # 2. Try to find standard markdown blocks
    if "```python" in text:
        text = text.split("```python")[-1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[-1].split("```")[0]

    # 3. Aggressive cleanup of conversational prose
    lines = text.split("\n")
    cleaned_lines = []
    start_collecting = False

    # Common starting points for Python scripts
    code_starters = ("import", "from", "def", "class", "qr", "df", "img")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if start_collecting:
                cleaned_lines.append(line)
            continue

        if any(stripped.startswith(s) for s in code_starters):
            start_collecting = True

        if start_collecting:
            # Stop if we hit conversational closing text
            if stripped.startswith(("Note:", "This script", "Hope this", "Here is")):
                break
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def generate_csv_python_code(user_input: str, csv_filename: str, csv_path: str) -> str:
    # We pass the specific CSV details into the prompt for the LLM
    prompt = f"""
    Task: {user_input}
    CSV Filename: {csv_filename}
    CSV Path: {csv_path}
    
    Please write the code to process this specific file.
    """

    # Format the system prompt with the actual csv_path
    formatted_system_prompt = SYSTEM_PROMPT.replace("{{csv_path}}", csv_path)

    response = llm.invoke(
        [SystemMessage(content=formatted_system_prompt), HumanMessage(content=prompt)]
    )

    return extract_code_from_llm_output(response.content)
