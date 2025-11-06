"""Minimal MCP-compatible server with a small calculator tool.

This file attempts to use `fastmcp`/`mcp` if installed. If not available,
it falls back to a small FastAPI app exposing a POST `/mcp` endpoint that
accepts JSON payloads with a `text` field and responds with a JSON result.

The fallback exposes `mcp.run(transport="sse")` so the snippet requested in
the assignment remains valid.
"""

from __future__ import annotations

import re
import json
from typing import Any

try:
	# Prefer real fastmcp if available
	import fastmcp as _fastmcp  # type: ignore
	# Use fastmcp only if it exposes a blocking `run` callable we can use
	if hasattr(_fastmcp, "run") and callable(getattr(_fastmcp, "run")):
		mcp = _fastmcp  # expose a module-like object for compatibility
	else:
		raise ImportError("fastmcp installed but does not provide a usable run() - falling back")
except Exception:
	# Fallback implementation using FastAPI/uvicorn
	from fastapi import FastAPI, Request
	import uvicorn

	class SimpleMCP:
		def __init__(self) -> None:
			self.app = FastAPI()

			@self.app.post("/mcp")
			async def handle(req: Request) -> Any:
				"""Handle incoming MCP-like requests.

				Expected JSON: {"text": "..."}
				Returns JSON: {"result": "..."}
				"""
				payload = await req.json()
				text = payload.get("text") or payload.get("message") or ""
				result = await self.handle_message(text)
				return {"result": result}

		async def handle_message(self, text: str) -> str:
			# Very small, safe calculator: look for "what is <expr>" or just an expression
			m = re.search(r"what is (.+)", text, re.I)
			expr = m.group(1) if m else text.strip()

			# Allow only digits, spaces and basic operators to avoid unsafe eval
			if not expr:
				return "no input"

			if re.match(r"^[0-9+\-*/(). \t]+$", expr):
				try:
					# Evaluate in a tiny restricted scope
					value = eval(expr, {"__builtins__": None}, {})
					return str(value)
				except Exception as e:
					return f"error: {e}"
			else:
				return "I can only calculate numeric expressions like 'what is 1+2'."

		def run(self, host: str = "127.0.0.1", port: int = 8000, transport: str = "sse") -> None:
			# transport arg accepted for compatibility with the requested snippet
			uvicorn.run(self.app, host=host, port=port)

	mcp = SimpleMCP()


if __name__ == "__main__":
	# Run the server (the user requested this exact snippet at the bottom)
	mcp.run(transport="sse")