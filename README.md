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

Notes

- The `server.py` prefers `fastmcp` if available, otherwise runs a small FastAPI app that accepts POST JSON payloads at `/mcp` with a `text` field.
- The calculator is intentionally conservative: it only evaluates expressions containing digits and + - * / ( ) to avoid arbitrary code execution.

# se333_finalproject
