import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()
WRITABLE_DIR = "/home/user"
llm = ChatGroq(model="llama-3.3-70b-versatile", groq_api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = f"""
You are a Python Expert. Your goal is to generate QR codes in a headless sandbox.

### BEGIN CODE

Rules:
1. MANDATORY EXECUTION: You must NOT just define functions. You MUST include a main execution block at the bottom of your script that calls your functions.
2. BASE64 PROTOCOL: To prevent binary corruption, you MUST print images as Base64.
   
   Use this exact structure:
   import qrcode
   import base64
   from io import BytesIO
   from PIL import Image

   def generate():
       qr = qrcode.QRCode(version=1, box_size=10, border=5)
       qr.add_data("URL_OR_DATA")
       img = qr.make_image().convert('RGB')
       
       # 1. Save to disk
       img.save("{WRITABLE_DIR}/qr_code.png", "PNG")
       
       # 2. Print Base64 for the controller
       buffered = BytesIO()
       img.save(buffered, format="PNG")
       img_str = base64.b64encode(buffered.getvalue()).decode()
       print(f"FILENAME:qr_code.png")
       print(f"BASE64:{{img_str}}")

   if __name__ == "__main__":
       generate()

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


def generate_python_code(user_input: str) -> str:
    response = llm.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_input)]
    )
    return extract_code_from_llm_output(response.content)
