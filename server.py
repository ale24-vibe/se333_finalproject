from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.responses import StreamingResponse
import uvicorn
import logging
import json
import re
import asyncio
from typing import Any, Dict

app = FastAPI()
logging.basicConfig(level=logging.INFO)

def _safe_eval(expr: str) -> str:
    """Evaluate a numeric expression consisting only of digits and basic operators.

    Returns a string result or raises a ValueError on invalid input.
    """
    if not re.match(r"^[0-9+\-*/(). \t]+$", expr):
        raise ValueError("invalid expression")
    try:
        value = eval(expr, {"__builtins__": None}, {})
    except Exception as e:
        raise ValueError(str(e))
    return str(value)

# No registered tools by default. This server runs minimally and does not expose tools.
TOOLS: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def sse_root():
    # Provide an SSE event stream so the MCP extension can connect for async notifications.
    async def event_stream():
        try:
            while True:
                # SSE comment keepalive (some clients prefer comments)
                yield ": keepalive\n\n"
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            return

    # Return the streaming response directly so clients can open an SSE connection.
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "se333_finalproject"}

@app.get("/tools")
async def tools_list():
    # Return empty list when no tools are registered to avoid advertising internal helpers.
    return {"tools": []}

def _make_rpc_response(req_body: Dict[str, Any], result_obj: Any) -> Any:
    if isinstance(req_body, dict) and req_body.get("jsonrpc") and "id" in req_body:
        return {"jsonrpc": "2.0", "id": req_body.get("id"), "result": result_obj}
    return {"result": result_obj}

@app.post("/")
async def handle(request: Request):
    """
    Handle JSON-RPC-ish POSTs from the MCP extension.
    - Reply immediately to 'initialize' with a minimal capabilities object.
    - Provide a simple 'what is 1+2' responder for smoke testing the tool.
    - Otherwise, echo back the params.
    """
    try:
        body = await request.json()
    except Exception:
        raw = await request.body()
        logging.info("Received non-JSON POST body: %s", raw)
        return JSONResponse({"jsonrpc":"2.0","error":{"code":-32700,"message":"Parse error"}}, status_code=400)

    logging.info("Received POST body: %s", json.dumps(body))
    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params", {})

    # Quick reply to initialize so VS Code will stop waiting
    if method == "initialize":
        result = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "capabilities": {
                    "name": "se333_server",
                    "version": "0.1"
                }
            }
        }
        logging.info("Responding to initialize")
        return JSONResponse(result)

    # Simple smoke-test handler: if params contain a text/question asking "what is 1+2"
    text = ""
    if isinstance(params, dict):
        # some clients may send the question in params.text or params.question
        text = params.get("text") or params.get("question") or ""
    elif isinstance(params, str):
        text = params

    if isinstance(text, str) and re.search(r"\bwhat is\s+1\s*\+\s*2\b", text, re.IGNORECASE):
        return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"answer":"3"}})

    # Generic echo response for other JSON-RPC requests to aid debugging
    return JSONResponse({"jsonrpc":"2.0","id":req_id,"result":{"echo": params}})

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        raw = await request.body()
        logging.info("Received non-JSON POST body: %s", raw)
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status_code=400)

    logging.info("POST /mcp body: %s", json.dumps(body))

    # JSON-RPC initialize
    if isinstance(body, dict) and body.get("method") == "initialize":
        # Advertise only neutral server capabilities; do not expose any tool names.
        res = {
            "status": "initialized",
            "tool_name": "se333_server",
            "version": "1.0",
            "description": "Minimal MCP-compatible server",
            "capabilities": [],
            "transport": "sse",
            "tools": []
        }
        return JSONResponse(_make_rpc_response(body, res))

    # Accept simple payloads {"text":"..."} or {"tool":"name","text":"..."}
    text = None
    tool = None
    if isinstance(body, dict):
        text = body.get("text") or body.get("message") or None
        tool = body.get("tool")
    # If body looks like JSON-RPC with params
    if isinstance(body, dict) and "params" in body:
        params = body.get("params") or {}
        if isinstance(params, dict):
            text = text or params.get("text") or params.get("message")
            tool = tool or params.get("tool")

    if not text:
        # Be lenient: return HTTP 200 but include a JSON-RPC-style error for RPC clients
        # so the MCP client doesn't treat this as an HTTP transport failure.
        if isinstance(body, dict) and body.get("jsonrpc"):
            rpc_err = {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {"code": -32602, "message": "no text provided"}
            }
            return JSONResponse(rpc_err, status_code=200)
        # Non-RPC clients: return a 200 with an error inside the result envelope.
        return JSONResponse(_make_rpc_response(body, {"error": "no text provided"}), status_code=200)

    # This server no longer dispatches to internal tools. Return helpful error/result.
    msg = {
        "error": "no tools available",
        "hint": "This server does not expose any tools. Start a different server or re-enable tools in server.py."
    }
    return JSONResponse(_make_rpc_response(body, msg), status_code=200)

if __name__ == "__main__":
    # Bind to localhost and port 8001 to match the configured MCP server URL.
    uvicorn.run("server:app", host="127.0.0.1", port=8001, log_level="info")
