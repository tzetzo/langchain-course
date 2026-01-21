# LangChain + MCP Multi-Server Agent

This project demonstrates a powerful Agentic AI architecture using LangGraph to orchestrate multiple Model Context Protocol (MCP) servers. It features a Python-based intelligent agent that communicates with modular tool servers written in Node.js.

## 🏗 Architecture Overview

The system follows a hub-and-spoke model where the LangGraph agent acts as the "brain," delegating specific tasks to specialized "workers" (MCP servers).

- **Orchestrator (Python)**: Uses LangGraph to manage conversation state and decision-making logic.
- **Transport (Stdio)**: The agent spawns Node.js servers as child processes and communicates via standard input/output.
- **Tool Servers (Node.js)**: Specialized servers for weather data and mathematical calculations.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ (managed via `uv` recommended)
- Node.js 18+
- Groq API Key

### 1. Setup MCP Servers (Node.js)

Navigate to your server directory (where `package.json` is located) and install dependencies:
```bash
npm install
```

### 2. Setup Agent (Python)

Install the Python environment and dependencies:
```bash
uv sync
```

### 3. Configuration

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_api_key_here
```

## 🎮 How to Run

### Running the Interactive App

To start the agent and begin an interactive chat session in your terminal:
```bash
uv run python run.py
```

Example queries to try:

- "What is the weather in Sofia and what is 1024 divided by 4?"
- "If the temperature in London is 15 degrees, what would it be if I multiplied it by 3?"

### Running the Tests

To verify the Python-to-Node.js bridge and ensure the graph logic is sound:
```bash
uv run pytest tests/test_graph.py
```

## 💡 How It Works

1. **Initialization**: The Python agent spawns Node.js processes. On Windows, it uses the `ProactorEventLoop` to manage these asynchronous pipes safely.

2. **Tool Discovery**: The agent queries each MCP server for its tool definitions and binds them to the LLM (Groq).

3. **The Reasoning Loop**:
   - The LLM receives a query and decides which tool to call.
   - The MCP client sends a JSON-RPC request to the Node.js server.
   - **Type Coercion**: The Node.js server uses `z.coerce.number()` to ensure that even if the LLM sends a number as a string (e.g., `"42"`), the math logic processes it correctly.
   - The result is returned to the LLM to provide a final answer.

## 🔧 Windows-Specific Handling

This project includes specific optimizations for Windows environments:

- **Proactor Event Loop**: Configured via `asyncio.WindowsProactorEventLoopPolicy` to prevent "Operation not supported" errors when handling subprocess pipes.
- **Graceful Shutdown**: Uses an `ExitStack` to ensure that when the Python app stops, the Node.js background processes are cleaned up properly.