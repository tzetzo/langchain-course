# controller.py

from agents.python_agent import python_agent
from agents.csv_agent import csv_agent


class ControllerResponse:
    """
    Unified response object returned by the controller.
    Makes it easy for Streamlit and LangGraph to consume results.
    """
    def __init__(self, logs: str, files: list[str]):
        self.logs = logs
        self.files = files

    def __repr__(self):
        return f"ControllerResponse(logs={len(self.logs)} chars, files={self.files})"


class CodeInterpreterController:
    """
    Main controller that routes tasks to the correct agent.
    """

    def run(self, user_input: str, file_bytes: bytes | None = None, filename: str | None = None) -> ControllerResponse:
        """
        Routes the request to the correct agent based on the presence and type of file.
        """

        # CASE 1 — CSV file uploaded → use CSV agent
        if file_bytes and filename and filename.lower().endswith(".csv"):
            result = csv_agent(
                user_input=user_input,
                csv_bytes=file_bytes,
                csv_filename=filename
            )
            return self._parse_agent_output(result)

        # CASE 2 — No file or non-CSV file → use Python agent
        result = python_agent(user_input)
        return self._parse_agent_output(result)

    # ---------------------------------------------------------
    # Helper: parse agent output into ControllerResponse
    # ---------------------------------------------------------

    def _parse_agent_output(self, raw_output: str) -> ControllerResponse:
        """
        Converts the raw string output from an agent into a structured response.
        """

        logs = raw_output
        files = []

        # Extract file paths from the output
        for line in raw_output.splitlines():
            if line.strip().startswith("- /home/user/"):
                files.append(line.strip().replace("- ", ""))

        return ControllerResponse(logs=logs, files=files)
