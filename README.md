# LangChain + MCP Multi-Server Agent

This project demonstrates a powerful Agentic AI architecture using LangGraph to orchestrate multiple Model Context Protocol (MCP) servers. It features a Python-based intelligent agent that communicates with modular tool servers written in Node.js, accessible via a modern web interface.

## 🏗 Architecture Overview

The system follows a hub-and-spoke model where the LangGraph agent acts as the "brain," delegating specific tasks to specialized "workers" (MCP servers).

- **Orchestrator (Python)**: Uses LangGraph to manage conversation state and decision-making logic.
- **Web UI (Chainlit)**: Provides a ChatGPT-like interface with real-time "Chain of Thought" visibility for tool execution.
- **Transport (Stdio)**: The agent spawns Node.js servers as child processes and communicates via standard input/output.
- **Tool Servers (Node.js)**: Specialized servers for Real-time Weather (Open-Meteo) and Universal Calculations.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ (managed via `uv` recommended)
- Node.js 18+
- Groq API Key

### 1. Setup MCP Servers (Node.js)

Navigate to your server directory and install dependencies:
```bash
npm install
```

### 2. Setup Agent (Python)

Install the Python environment and dependencies:
```bash
uv sync
uv add chainlit
```

### 3. Configuration

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_api_key_here
```

## 🎮 How to Run

### Option A: Web UI (Recommended)

Start the professional web interface. This provides the best experience, showing tool execution steps in real-time.
```bash
uv run chainlit run app_ui.py -w
```

Your app will be available at: http://localhost:8000

### Option B: Terminal CLI

To start a lightweight interactive session directly in your terminal:
```bash
uv run python run.py
```

### Running the Tests

To verify the Python-to-Node.js bridge and tool reliability:
```bash
uv run pytest tests/test_graph.py
```

## 💡 How It Works

1. **Initialization**: The Python agent spawns Node.js processes. On Windows, it uses the `ProactorEventLoop` to manage asynchronous pipes safely.

2. **Tool Discovery**: The agent queries each MCP server for its tool definitions and binds them to the LLM (Groq) using a specialized System Message to ensure high-quality tool calls.

3. **The Reasoning Loop**:
   - The LLM receives a query and decides which tool to call.
   - **Type Safety**: To support the Groq API's strict validation, the Calculator server uses a Flexible Zod Schema (`z.any()` + transform) to handle cases where the LLM might send numbers as strings.
   - **Live Data**: The Weather server fetches real-time data from the Open-Meteo API using geocoding.

## 🔧 Windows-Specific Handling

This project includes optimizations for Windows environments:

- **Proactor Event Loop**: Configured via `asyncio.WindowsProactorEventLoopPolicy()` to prevent "Operation not supported" errors when handling subprocess pipes.
- **Process Cleanup**: Explicit shutdown logic in `mcp_client.py` ensures Node.js child processes are terminated when the UI or CLI stops.