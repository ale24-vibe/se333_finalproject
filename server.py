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
import re
import json
import asyncio
import logging
from typing import Any

# Registry for decorated MCP tools: list of (name, func)
_registered_mcp_functions: list[tuple[str, Any]] = []

def mcp(func=None, name: str | None = None):
    """Decorator to register a function as an MCP tool.

    Usage:
      @mcp
      def foo(text): ...

      or

      @mcp(name="calc")
      def bar(text): ...
    """
    if func is None:
        def _decorator(f):
            _registered_mcp_functions.append((name or f.__name__, f))
            return f
        return _decorator
    else:
        _registered_mcp_functions.append((name or getattr(func, "__name__", "tool"), func))
        return func

# Basic logging setup
logger = logging.getLogger("apletest")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger.setLevel(logging.INFO)


# Example usage: register a small calculator tool via the @mcp decorator.
@mcp
def aple_calculator(text: str) -> str:
    """Simple decorated calculator used as a named tool.
    Returns the numeric result as a string.
    """
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
    return "I can only calculate numeric expressions like 'what is 1+2'."

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
                logger.info("/mcp request: %s", payload)
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
                # Dispatch by named tool if provided
                tool_name = payload.get("tool")
                if tool_name and hasattr(self, "tools") and tool_name in self.tools:
                    func = self.tools[tool_name]
                    if asyncio.iscoroutinefunction(func):
                        result = await func(text)
                    else:
                        result = func(text)
                else:
                    # Prefer an instance-level `handle_message` if installed (e.g. via @mcp)
                    handler = getattr(self, "handle_message", None)
                    if handler and callable(handler):
                        result = await handler(text)
                    else:
                        result = await handle_message_text(text)
                return {"result": result}

            @self.app.post("/")
            async def handle_root_post(req: Request) -> Any:
                payload = await req.json()
                logger.info("/ (root POST) request: %s", payload)
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
                tool_name = payload.get("tool")
                if tool_name and hasattr(self, "tools") and tool_name in self.tools:
                    func = self.tools[tool_name]
                    if asyncio.iscoroutinefunction(func):
                        result = await func(text)
                    else:
                        result = func(text)
                else:
                    handler = getattr(self, "handle_message", None)
                    if handler and callable(handler):
                        result = await handler(text)
                    else:
                        result = await handle_message_text(text)
                return {"result": result}

            @self.app.post("/initialize")
            async def handle_initialize(req: Request) -> Any:
                payload = await req.json()
                logger.info("/initialize request: %s", payload)
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

            @self.app.get("/tools")
            async def tools_list() -> Any:
                # Return list of registered tools (name and brief description)
                tools = []
                if hasattr(self, "tools"):
                    for name, func in self.tools.items():
                        tools.append({
                            "name": name,
                            "doc": func.__doc__ or "",
                        })
                return {"tools": tools}

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
    # Build a mapping of name -> function and attach to the instance for dispatch
    tools_map = {}
    for name, func in _registered_mcp_functions:
        tools_map[name] = func
    mcp.tools = tools_map
    # Install the first registered function as the default handler
    first_name, first_func = _registered_mcp_functions[0]
    if asyncio.iscoroutinefunction(first_func):
        mcp.handle_message = first_func  # type: ignore
    else:
        async def _wrap(text: str, _f=first_func) -> str:
            return _f(text)
        mcp.handle_message = _wrap  # type: ignore

if __name__ == "__main__":
    mcp.run(transport="sse")
