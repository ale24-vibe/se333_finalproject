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

_registered_mcp_functions: list = []

def mcp(func=None):
    if func is None:
        def _decorator(f):
            _registered_mcp_functions.append(f)
            return f
        return _decorator
    else:
        _registered_mcp_functions.append(func)
        return func

try:
    import fastmcp as _fastmcp  # type: ignore
    if hasattr(_fastmcp, "run") and callable(getattr(_fastmcp, "run")):
        mcp = _fastmcp
    else:
        raise ImportError("fastmcp installed but does not provide a usable run() - falling back")
except Exception:
    from fastapi import FastAPI, Request
    from fastapi.responses import StreamingResponse, JSONResponse
    import uvicorn

    class SimpleMCP:
        def __init__(self) -> None:
            self.app = FastAPI()

            async def handle_message_text(text: str) -> str:
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

            @self.app.post("/mcp")
            async def handle_mcp(req: Request) -> Any:
                payload = await req.json()
                if isinstance(payload, dict) and payload.get("method") == "initialize":
                    return {
                        "result": {
                            "status": "initialized",
                            "tool_name": "ApleTest",
                            "version": "1.0",
                            "description": "Minimal calculator tool for MCP-compatible clients",
                            "capabilities": ["calculate", "evaluate expressions"],
                            "transport": "sse"
                        }
                    }
                text = payload.get("text") or payload.get("message") or ""
                result = await handle_message_text(text)
                return {"result": result}

            @self.app.post("/")
            async def handle_root_post(req: Request) -> Any:
                payload = await req.json()
                if isinstance(payload, dict) and payload.get("method") == "initialize":
                    return {
                        "result": {
                            "status": "initialized",
                            "tool_name": "ApleTest",
                            "version": "1.0",
                            "description": "Minimal calculator tool for MCP-compatible clients",
                            "capabilities": ["calculate", "evaluate expressions"],
                            "transport": "sse"
                        }
                    }
                text = payload.get("text") or payload.get("message") or ""
                result = await handle_message_text(text)
                return {"result": result}

            @self.app.post("/initialize")
            async def handle_initialize(req: Request) -> Any:
                _ = await req.json()
                return {
                    "result": {
                        "status": "initialized",
                        "tool_name": "ApleTest",
                        "version": "1.0",
                        "description": "Minimal calculator tool for MCP-compatible clients",
                        "capabilities": ["calculate", "evaluate expressions"],
                        "transport": "sse"
                    }
                }

            @self.app.get("/metadata")
            async def metadata() -> Any:
                return {
                    "tool_name": "ApleTest",
                    "version": "1.0",
                    "description": "Minimal calculator tool for MCP-compatible clients",
                    "capabilities": ["calculate", "evaluate expressions"],
                    "mcp_compatible": True
                }

            @self.app.get("/")
            async def sse_root():
                async def event_stream():
                    try:
                        while True:
                            yield ": keepalive\n\n"
                            await asyncio.sleep(15)
                    except asyncio.CancelledError:
                        return
                return StreamingResponse(event_stream(), media_type="text/event-stream")

            @self.app.get("/health")
            async def health() -> Any:
                return {"status": "ok", "service": "ApleTest"}

        async def handle_message(self, text: str) -> str:
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
            uvicorn.run(self.app, host=host, port=port)

    mcp = SimpleMCP()

if _registered_mcp_functions:
    _f = _registered_mcp_functions[0]
    if asyncio.iscoroutinefunction(_f):
        mcp.handle_message = _f  # type: ignore
    else:
        async def _wrap(text: str, _f=_f) -> str:
            return _f(text)
        mcp.handle_message = _wrap  # type: ignore

if __name__ == "__main__":
    mcp.run(transport="sse")
