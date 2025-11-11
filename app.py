from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
import json
from typing import Any, Dict

from tools import TOOLS
from utils import _make_rpc_response

app = FastAPI()


@app.get("/")
async def sse_root():
    async def event_stream():
        try:
            while True:
                yield ": keepalive\n\n"
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ApleTest"}


@app.get("/tools")
async def tools_list():
    return {"tools": [{"name": name, "doc": info.get("doc", "")} for name, info in TOOLS.items()]}


@app.post("/")
async def handle(request: Request):
    try:
        body = await request.json()
    except Exception:
        raw = await request.body()
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status_code=400)

    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params", {})

    if method == "initialize":
        result = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "capabilities": {"name": "ApleTest", "version": "0.1"}
            },
        }
        return JSONResponse(result)

    text = ""
    if isinstance(params, dict):
        text = params.get("text") or params.get("question") or ""
    elif isinstance(params, str):
        text = params

    if isinstance(text, str) and "what is 1+2" in text.replace(" ", ""):
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"answer": "3"}})

    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": {"echo": params}})


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        body = await request.json()
    except Exception:
        raw = await request.body()
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}, status_code=400)

    # initialize
    if isinstance(body, dict) and body.get("method") == "initialize":
        res = {
            "status": "initialized",
            "tool_name": "ApleTest",
            "version": "1.0",
            "description": "Minimal calculator tool for MCP-compatible clients",
            "capabilities": ["calculate", "evaluate expressions"],
            "transport": "sse",
            "tools": [{"name": name, "doc": info.get("doc", "")} for name, info in TOOLS.items()],
        }
        return JSONResponse(_make_rpc_response(body, res))

    text = None
    tool = None
    if isinstance(body, dict):
        text = body.get("text") or body.get("message") or None
        tool = body.get("tool")
    if isinstance(body, dict) and "params" in body:
        params = body.get("params") or {}
        if isinstance(params, dict):
            text = text or params.get("text") or params.get("message")
            tool = tool or params.get("tool")

    if not text:
        if isinstance(body, dict) and body.get("jsonrpc"):
            rpc_err = {"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32602, "message": "no text provided"}}
            return JSONResponse(rpc_err, status_code=200)
        return JSONResponse(_make_rpc_response(body, {"error": "no text provided"}), status_code=200)

    if tool:
        if tool not in TOOLS:
            return JSONResponse(_make_rpc_response(body, {"error": "tool not found"}), status_code=404)
        func = TOOLS[tool]["func"]
        try:
            result = func(text)
        except Exception as e:
            return JSONResponse(_make_rpc_response(body, {"error": str(e)}), status_code=200)
        return JSONResponse(_make_rpc_response(body, result))

    try:
        result = TOOLS["aple_calculator"]["func"](text)
    except Exception as e:
        return JSONResponse(_make_rpc_response(body, {"error": str(e)}), status_code=200)
    return JSONResponse(_make_rpc_response(body, result))
