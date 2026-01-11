import os
import logging
import re
import base64
from dataclasses import dataclass
from typing import List, Optional

from e2b_code_interpreter import Sandbox
from agents.python_agent import generate_python_code, extract_code_from_llm_output
from agents.csv_agent import generate_csv_python_code

# The absolute source of truth for the writable directory
WRITABLE_DIR = "/home/user"

logger = logging.getLogger(__name__)


@dataclass
class GeneratedFile:
    name: str
    path: str
    data: bytes


@dataclass
class ControllerResponse:
    logs: str
    files: List[GeneratedFile]


class CodeInterpreterController:
    def run(
        self,
        user_input: str,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
    ) -> ControllerResponse:
        sandbox = Sandbox.create(api_key=os.environ["E2B_API_KEY"])
        logger.info("Sandbox started.")

        try:
            csv_path_in_sandbox: Optional[str] = None
            if file_bytes and filename:
                csv_path_in_sandbox = f"{WRITABLE_DIR}/{filename}"
                sandbox.files.write(csv_path_in_sandbox, file_bytes)

            # Get code from agents
            if csv_path_in_sandbox and filename.lower().endswith(".csv"):
                raw_llm_output = generate_csv_python_code(
                    user_input, filename, csv_path_in_sandbox
                )
            else:
                raw_llm_output = generate_python_code(user_input)

            # Clean the code from prose/markdown
            code = extract_code_from_llm_output(raw_llm_output)

            # Force absolute paths in case AI hallucinations
            code = self._normalize_paths_in_code(code)

            # Execute code and get logs
            logs = self._run_code_with_auto_install(sandbox, code)

            # COLLECT FILES: Pass logs into the collector for Base64 scraping
            files = self._collect_generated_files(sandbox, logs)

            return ControllerResponse(logs=logs, files=files)

        finally:
            logger.info("Killing sandbox.")
            sandbox.kill()

    def _run_code_with_auto_install(self, sandbox: Sandbox, code: str) -> str:
        execution = sandbox.run_code(code)

        if execution.error and execution.error.name == "ModuleNotFoundError":
            match = re.search(r"No module named '([^']+)'", execution.error.value)
            missing = match.group(1) if match else None

            if missing:
                pkg = "qrcode[pil] Pillow" if missing == "qrcode" else missing
                logger.warning(f"Installing: {pkg}")
                sandbox.commands.run(f"pip install {pkg}")
                execution = sandbox.run_code(code)

        return self._format_execution_logs(execution)

    def _collect_generated_files(
        self, sandbox: Sandbox, logs: str
    ) -> List[GeneratedFile]:
        collected_files: List[GeneratedFile] = []
        seen_names = set()

        # --- METHOD 1: BASE64 SCRAPING (The Primary Fix) ---
        # Look for the FILENAME:xxx and BASE64:yyy pattern in logs
        # This is immune to file-system encoding corruption
        base64_pattern = r"FILENAME:(.*?)\nBASE64:(.*?)(?:\n|$)"
        matches = re.findall(base64_pattern, logs, re.DOTALL)

        for name_match, b64_data in matches:
            try:
                name = name_match.strip()
                # Remove all whitespace/newlines from the b64 string
                clean_b64 = "".join(b64_data.split())
                byte_data = base64.b64decode(clean_b64)

                if byte_data:
                    collected_files.append(
                        GeneratedFile(name=name, path="memory", data=byte_data)
                    )
                    seen_names.add(name)
                    logger.info(f"Successfully scraped {name} from logs via Base64.")
            except Exception as b64_err:
                logger.error(f"Base64 decode failed for {name_match}: {b64_err}")

        # --- METHOD 2: FILE SYSTEM (Fallback) ---
        try:
            entries = sandbox.files.list(WRITABLE_DIR)
            for entry in entries:
                name = os.path.basename(entry.path)
                if entry.type == "dir" or name.startswith(".") or name in seen_names:
                    continue

                raw_data = sandbox.files.read(entry.path)
                if not raw_data:
                    continue

                # Re-encode string to bytes using latin-1 to avoid data loss
                byte_data = (
                    raw_data.encode("latin-1", errors="ignore")
                    if isinstance(raw_data, str)
                    else raw_data
                )

                # Final "Ghost Byte" check for files on disk
                if byte_data.startswith(b"PNG\r\n\x1a\n"):
                    byte_data = b"\x89" + byte_data

                collected_files.append(
                    GeneratedFile(name=name, path=entry.path, data=byte_data)
                )
        except Exception as e:
            logger.error(f"File system fallback failed: {e}")

        return collected_files

    def _normalize_paths_in_code(self, code: str) -> str:
        for bad_path in ["/mnt/data", "/workspace", "./", "output/"]:
            code = code.replace(bad_path, f"{WRITABLE_DIR}/")
        return code.replace("//", "/")

    def _format_execution_logs(self, execution) -> str:
        logs = []
        if execution.logs.stdout:
            logs.append("".join(execution.logs.stdout))
        if execution.logs.stderr:
            logs.append("".join(execution.logs.stderr))
        if execution.error:
            logs.append(execution.error.traceback)
        return "\n".join(logs) if logs else "Success (no output)."
