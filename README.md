# MCP Server and dev setup

This project contains a minimal MCP-compatible server and instructions to set up a virtual environment for development and testing with VS Code MCP integration.

Quick start

1. Create a venv (recommended):

	python -m venv .venv
	source .venv/bin/activate

2. Install dependencies (from project root):

	pip install -e .

	or explicitly:
	pip install fastapi uvicorn httpx fastmcp mcp[cli]

3. Run the server:

	python server.py

4. In VS Code: Press Ctrl+Shift+P → MCP: Add Server and paste the server URL (e.g. http://127.0.0.1:8000/mcp or http://127.0.0.1:8000). Give it a name and press Enter.

5. Test in the Chat view: "what is 1+2" should return the correct result.

Discovery and named tools

- The server exposes a discovery endpoint at GET /tools which returns a list of registered tool names. Example:

	curl -s http://127.0.0.1:8001/tools | jq

- You can dispatch to a specific tool by including a "tool" field in the POST payload to /mcp. Example:

	curl -s -X POST http://127.0.0.1:8001/mcp -H 'Content-Type: application/json' -d '{"tool":"aple_calculator","text":"what is 1+2"}' | jq

VS Code launch

Open the Run view in VS Code and use the "Run ApleTest server" configuration to start the server from the editor.

Logging

The server logs initialize and MCP requests to the console, so watch the terminal panel or the output captured by the VS Code Run view while debugging.

Notes

- The `server.py` prefers `fastmcp` if available, otherwise runs a small FastAPI app that accepts POST JSON payloads at `/mcp` with a `text` field.
- The calculator is intentionally conservative: it only evaluates expressions containing digits and + - * / ( ) to avoid arbitrary code execution.

# se333_finalproject
