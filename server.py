"""Compatibility runner: start the FastAPI app defined in `app.py`.

This file preserves the existing entrypoint so external tooling and
launch configurations that point to `server.py` continue to work.
"""
import uvicorn


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8001, log_level="info")
