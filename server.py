from fastmcp import FastMCP
import subprocess
import shlex
import signal
import sys
import time
import threading

# Create MCP instance
mcp = FastMCP("Calculator MCP Server")

@mcp.tool(description="Adds two integers")
def add(a: int, b: int) -> int:
    return a + b

@mcp.tool(description="Subtracts b from a")
def subtract(a: int, b: int) -> int:
    return a - b

@mcp.tool(description="Multiplies two integers")
def multiply(a: int, b: int) -> int:
    return a * b

@mcp.tool(description="Divides a by b (returns float, inf if b=0)")
def divide(a: int, b: int) -> float:
    return a / b if b != 0 else float("inf")


@mcp.tool(description="Generate JUnit tests from Java sources (runs .mcp/generate_tests.py)")
def generate_tests() -> str:
    """Run the test generator script and return its stdout/stderr."""
    cmd = ["python3", ".mcp/generate_tests.py"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout.strip()
    err = p.stderr.strip()
    return ("OK:\n" + out) if p.returncode == 0 else ("ERROR:\n" + err + "\n" + out)


@mcp.tool(description="Run Maven tests (mvn -U clean test)")
def run_tests() -> str:
    """Run mvn tests and return build output (stdout/stderr)."""
    cmd = ["mvn", "-U", "clean", "test"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout + "\n" + p.stderr
    prefix = "OK" if p.returncode == 0 else f"FAIL (code {p.returncode})"
    return prefix + ":\n" + out


@mcp.tool(description="Analyze JaCoCo coverage and return recommendations")
def analyze_coverage() -> str:
    """Run the coverage analyzer script and return its output."""
    cmd = ["python3", ".mcp/coverage_analyzer.py"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout + "\n" + p.stderr
    return out.strip()


def _graceful_shutdown(signum=None, frame=None):
    """Attempt to shut down the MCP server cleanly.

    This will try to call a shutdown method on the `mcp` instance if available.
    If that is not present or fails, exit the process. This function is safe to
    call from a signal handler.
    """
    try:
        print("Shutting down ApleTest server...")
        # try synchronous shutdown method if present
        if hasattr(mcp, "shutdown"):
            try:
                mcp.shutdown()
            except Exception:
                # best-effort; ignore errors
                pass
        # if there is an async close API, we can't await it here; just wait a bit
        time.sleep(0.2)
    except Exception:
        pass
    finally:
        # ensure we exit with 0 for a clean Ctrl+C shutdown
        try:
            sys.exit(0)
        except SystemExit:
            # re-raise to terminate
            raise


# Run the server when executing this file
if __name__ == "__main__":
    # register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, _graceful_shutdown)
    signal.signal(signal.SIGTERM, _graceful_shutdown)
    # Ask whether to run Maven tests after starting the server
    try:
        resp = input("Start server first, then run 'mvn -U clean test'? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        resp = "n"
    run_maven = resp in ("y", "yes")
    run_in_background = False
    if run_maven:
        try:
            bg = input("Run Maven in background (non-blocking)? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            bg = "n"
        run_in_background = bg in ("y", "yes")

    # Start the MCP server in a background thread so we can run mvn after it starts
    def _run_server():
        try:
            mcp.run(transport="sse", host="127.0.0.1", port=8001)
        except Exception:
            # if server stops due to an exception, print and exit thread
            print("ApleTest server stopped with an exception.")

    server_thread = threading.Thread(target=_run_server, name="ApleTestServerThread", daemon=True)
    server_thread.start()
    print("ApleTest server started (thread: ApleTestServerThread).")

    # Optionally run Maven tests now
    if run_maven:
        if run_in_background:
            try:
                subprocess.Popen(["mvn", "-U", "clean", "test"], stdout=None, stderr=None)
                print("Maven started in background.")
            except Exception as e:
                print(f"Failed to start Maven in background: {e}")
        else:
            try:
                print("Running mvn -U clean test (foreground, streaming output)...")
                subprocess.run(["mvn", "-U", "clean", "test"], check=False)
            except Exception as e:
                print(f"Error running mvn: {e}")

    # Wait for server thread to finish (server runs until interrupted)
    try:
        while server_thread.is_alive():
            server_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        _graceful_shutdown()
    try:
        mcp.run(transport="sse", host="127.0.0.1", port=8001)
    except KeyboardInterrupt:
        # fallback if signal didn't fire inside anyio
        _graceful_shutdown()
