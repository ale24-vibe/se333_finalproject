from fastmcp import FastMCP
import subprocess
import shlex
import signal
import sys
import time
import threading
from git_tools import GitAutomation, WorkflowIntegration, GitStatus

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


# ============================================================================
# GIT AUTOMATION TOOLS
# ============================================================================

# Initialize git tools
git_automation = GitAutomation(".")
workflow = WorkflowIntegration(".")


@mcp.tool(description="Get current git repository status")
def git_status() -> dict:
    """
    Return git status including staged/unstaged changes and conflicts.
    
    Returns a dict with:
    - is_clean: Whether repo is clean
    - staged_files: List of staged changes
    - unstaged_files: List of unstaged changes
    - conflicts: List of conflicted files
    - current_branch: Current branch name
    - untracked_files: List of untracked files
    """
    try:
        status = git_automation.git_status()
        return {
            "success": True,
            "is_clean": status.is_clean,
            "staged_files": status.staged_files,
            "unstaged_files": status.unstaged_files,
            "conflicts": status.conflicts,
            "current_branch": status.current_branch,
            "untracked_files": status.untracked_files,
            "message": "Repository is clean" if status.is_clean else "Repository has changes"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting git status: {str(e)}"
        }


@mcp.tool(description="Stage all changes with intelligent filtering")
def git_add_all(exclude_patterns: list = None) -> dict:
    """
    Stage all changes, excluding build artifacts and temporary files.
    
    Args:
        exclude_patterns: Optional list of glob patterns to exclude
        
    Returns a dict with staging result and count of staged files.
    """
    try:
        result = git_automation.git_add_all(exclude_patterns)
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Error staging changes: {str(e)}"
        }


@mcp.tool(description="Commit staged changes with optional coverage statistics")
def git_commit(message: str, coverage_stats: dict = None) -> dict:
    """
    Commit staged changes with standardized message and optional coverage stats.
    
    Args:
        message: Commit message
        coverage_stats: Optional dict of coverage statistics to include
        
    Returns a dict with commit result, hash, and success status.
    """
    try:
        result = git_automation.git_commit(message, coverage_stats)
        return {
            "success": result.success,
            "message": result.message,
            "commit_hash": result.commit_hash
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error committing: {str(e)}"
        }


@mcp.tool(description="Push commits to remote with upstream configuration")
def git_push(remote: str = "origin", branch: str = None) -> dict:
    """
    Push commits to remote repository.
    
    Args:
        remote: Remote name (default: origin)
        branch: Branch to push (default: current branch)
        
    Returns a dict with push result and success status.
    """
    try:
        result = git_automation.git_push(remote, branch)
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Error pushing: {str(e)}"
        }


@mcp.tool(description="Create a pull request on GitHub")
def git_pull_request(
    base: str = "main",
    title: str = None,
    body: str = None,
    coverage_stats: dict = None
) -> dict:
    """
    Create a pull request against the specified base branch.
    Requires GitHub CLI (gh) to be installed and authenticated.
    
    Args:
        base: Base branch for PR (default: main)
        title: PR title (auto-generated if not provided)
        body: PR description
        coverage_stats: Optional coverage statistics to include
        
    Returns a dict with PR URL, number, and success status.
    """
    try:
        result = git_automation.git_pull_request(base, title, body, coverage_stats)
        return {
            "success": result.success,
            "message": result.message,
            "pr_url": result.pr_url,
            "pr_number": result.pr_number
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating PR: {str(e)}"
        }


@mcp.tool(description="Execute full automated workflow: stage → commit → push → optional PR")
def automated_workflow(
    commit_message: str,
    push_remote: str = "origin",
    create_pr: bool = False,
    pr_base: str = "main",
    pr_title: str = None,
    coverage_stats: dict = None
) -> dict:
    """
    Execute full automated git workflow in sequence.
    
    Args:
        commit_message: Message for the commit
        push_remote: Remote to push to (default: origin)
        create_pr: Whether to create a PR after push
        pr_base: Base branch for PR (default: main)
        pr_title: Title for PR (auto-generated if not provided)
        coverage_stats: Optional coverage statistics
        
    Returns a dict with results of each workflow step.
    """
    try:
        result = workflow.automated_workflow(
            commit_message,
            push_remote,
            create_pr,
            pr_base,
            pr_title,
            coverage_stats
        )
        return {"success": True, "workflow_steps": result}
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in workflow: {str(e)}"
        }
    
@mcp.tool(description="Create a trivial change, commit, and optionally push")
def create_and_commit(
    message: str = "chore: automated test commit",
    file_path: str = ".autocommit",
    content: str = None,
    push: bool = True,
    push_remote: str = "origin",
    create_branch: str = None
) -> dict:
    """
    Create or append a small change to `file_path`, stage, commit, and optionally push.
    - `content`: optional string to write; if None, a timestamped line is appended.
    - `push`: whether to run git_push after commit.
    - `create_branch`: optional branch name to create and switch to before making changes.
    Returns a dict with step results.
    """
    import datetime
    from pathlib import Path

    try:
        # Optionally create/check out a feature branch
        if create_branch:
            # Try to create branch; if already exists, checkout it
            rc, out, err = git_automation._run_git(["checkout", "-b", create_branch])
            if rc != 0:
                git_automation._run_git(["checkout", create_branch])

        # Prepare content
        if content is None:
            content = f"autocommit: {datetime.datetime.utcnow().isoformat()}\n"

        # Write/append to file
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(content)

        # Stage changes
        stage_result = git_add_all()
        if not stage_result.get("success", False):
            return {"success": False, "step": "stage", "detail": stage_result}

        # Commit
        commit_result = git_commit(message)
        if not commit_result.get("success", False):
            return {"success": False, "step": "commit", "detail": commit_result}

        result = {"success": True, "stage": stage_result, "commit": commit_result}

        # Push (optional)
        if push:
            push_result = git_push(push_remote)
            result["push"] = push_result
            if not push_result.get("success", False):
                result["push_failed"] = True

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}

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
