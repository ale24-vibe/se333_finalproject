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

3. Run the server (uses `server.py` compat runner):

	/Users/alexle/SE Final Project/.venv/bin/python /Users/alexle/SE Final Project/server.py

4. In VS Code: Press Ctrl+Shift+P → MCP: Add Server and paste the server URL (e.g. http://127.0.0.1:8001/mcp). Give it a name and press Enter.

5. Test in the Chat view: example prompts shown below.

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

- The server runs a FastAPI app that accepts POST JSON payloads at `/mcp` with a `text` field or JSON-RPC bodies.
- The calculator evaluates expressions safely (digits and operators only). NLP normalization supports common math words and number words (e.g., "two times three").

# se333_finalproject
