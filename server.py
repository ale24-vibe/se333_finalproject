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
import asyncio
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
	from fastapi.responses import StreamingResponse, JSONResponse
	import uvicorn

	class SimpleMCP:
		def __init__(self) -> None:
			self.app = FastAPI()

			async def handle_message_text(text: str) -> str:
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

			@self.app.post("/mcp")
			async def handle_mcp(req: Request) -> Any:
				"""Handle incoming MCP-like requests.

				Expected JSON: {"text": "..."}
				Returns JSON: {"result": "..."}
				"""
				payload = await req.json()
				text = payload.get("text") or payload.get("message") or ""
				result = await handle_message_text(text)
				return {"result": result}

			# Accept POSTs at the root path too — some MCP clients POST to `/`
			@self.app.post("/")
			async def handle_root_post(req: Request) -> Any:
				payload = await req.json()
				text = payload.get("text") or payload.get("message") or ""
				result = await handle_message_text(text)
				return {"result": result}

			# Provide a minimal SSE GET endpoint so clients that fall back to
			# legacy SSE can connect to `/` as an event stream. This generator
			# yields periodic keepalive comments so the connection stays open.
			async def event_stream():
				try:
					while True:
						# SSE comment (keeps connection alive)
						yield ": keepalive\n\n"
						await asyncio.sleep(15)
				except asyncio.CancelledError:
					return

			@self.app.get("/")
			async def sse_root():
				return StreamingResponse(event_stream(), media_type="text/event-stream")

			# Minimal health endpoint for tooling to probe availability.
			@self.app.get("/health")
			async def health() -> Any:
				return {"status": "ok", "service": "ApleTest"}

		async def handle_message(self, text: str) -> str:
			# kept for compatibility if other code calls mcp.handle_message
			m = re.search(r"what is (.+)", text, re.I)
			expr = m.group(1) if m else text.strip()

			if not expr:
				return "no input"

			if re.match(r"^[0-9+\-*/(). \t]+$", expr):
				try:
					value = eval(expr, {"__builtins__": None}, {})
					return str(value)
				except Exception as e:
					return f"error: {e}"
			else:
				return "I can only calculate numeric expressions like 'what is 1+2'."

		def run(self, host: str = "127.0.0.1", port: int = 8001, transport: str = "sse") -> None:
			# transport arg accepted for compatibility with the requested snippet
			uvicorn.run(self.app, host=host, port=port)


	mcp = SimpleMCP()


if __name__ == "__main__":
	# Run the server (the user requested this exact snippet at the bottom)
	mcp.run(transport="sse")