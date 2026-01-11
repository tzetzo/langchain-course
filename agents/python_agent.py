import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
WRITABLE_DIR = "/home/user"
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = f"""
You are a versatile Python Expert. Your goal is to solve the user's request using Python code in a sandbox.

### BEGIN CODE

Rules:
1. GENERAL PURPOSE: Only generate QR codes if the user explicitly asks for them. Otherwise, perform the task requested (e.g., data analysis, calculations, text manipulation).
2. Writable Directory: Always save files to {WRITABLE_DIR}.
3. BINARY PROTOCOL (ONLY if generating images):
   If the user asks for QR codes or images, you MUST use Base64 to prevent corruption:
   - Encode the PIL image to Base64.
   - Print using: FILENAME:name.png and BASE64:string.

   Example for QR:
   import qrcode, base64, io
   img = qrcode.make("data").convert('RGB')
   buf = io.BytesIO()
   img.save(buf, format="PNG")
   print(f"FILENAME:qr.png\\nBASE64:{{base64.b64encode(buf.getvalue()).decode()}}")

4. NO MARKDOWN: Provide raw code only.
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


def generate_python_code(user_input: str) -> str:
    response = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_input)]
    )
    return extract_code_from_llm_output(response.content)
