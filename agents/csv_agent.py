import os
import re
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

WRITABLE_DIR = "/home/user"
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = f"""
You are a Data Science Assistant specializing in batch QR codes.

### BEGIN CODE

Rules:
1. Data Access: CSV is at {{csv_path}}. Use `pd.read_csv('{{csv_path}}')`.
2. BATCH BASE64 PROTOCOL: Iterate through the rows and print each image as Base64.
   
   Structure:
   import pandas as pd
   import qrcode
   import base64
   from io import BytesIO

   def process_csv():
       df = pd.read_csv('{{csv_path}}')
       for index, row in df.iterrows():
           content = str(row.iloc[0])
           qr = qrcode.make(content).convert('RGB')
           
           # Encode to Base64
           buf = BytesIO()
           qr.save(buf, format="PNG")
           b64 = base64.b64encode(buf.getvalue()).decode()
           
           fname = f"qr_{{index}}.png"
           qr.save(f"{WRITABLE_DIR}/{{fname}}", "PNG")
           print(f"FILENAME:{{fname}}")
           print(f"BASE64:{{b64}}")

   if __name__ == "__main__":
       process_csv()

3. Constraints: No markdown backticks. Save to {WRITABLE_DIR}.
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
